#!/usr/bin/env node
// stock-recap / gather.mjs
// Pulls every TraderDaddy Pro screener + flow + new CBOE option listings, plus
// TickerTrace 13F hedge-fund activity, builds a convergence-ranked shortlist,
// and writes a markdown report + raw JSON snapshots under runs/<timestamp>/.
//
// Auth: AGENT_API_KEY (read from repo-root .env_agent_api or env) for /api/agent/*.
// Screeners, options-listings and TickerTrace are public (no key needed).
// Runs on Node 18+ (uses global fetch). No external deps.

import { writeFile, mkdir, readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');

// ---- config ---------------------------------------------------------------
const TD_BASE = process.env.TD_API_URL || 'https://traderdaddy-pro-whop-production.up.railway.app';
const TT_BASE = process.env.TICKERTRACE_API_URL || 'https://api.tickertrace.pro/api/v1';
// NEW dev API (api.traderdaddy.pro/api/v1, X-API-Key td_live_*) — backs the
// week-ahead calendar (earnings + econ), GEX regime, and sector flow. Distinct
// from the OLD Railway agent API above; key lives in repo-root .env_td_api.
const DEV_BASE = process.env.TD_DEV_API_URL || 'https://api.traderdaddy.pro/api/v1';
const TIMEOUT_MS = Number(process.env.RECAP_TIMEOUT_MS || 60000);
const SCREENER_CONCURRENCY = 4;
const SHORTLIST_SIZE = Number(process.env.RECAP_SHORTLIST || 15);

// Window for time-bounded legs (flow). 'today' = daily recap; RECAP_WINDOW=week
// is the Sunday-night weekly pull (weekly flow is noisier, so thresholds tighten).
const RECAP_WINDOW = (process.env.RECAP_WINDOW || 'today').toLowerCase();
const IS_WEEKLY = RECAP_WINDOW === 'week';

// Flow thresholds (the "biggest flows" filter)
const FLOW_MIN_SCORE = Number(process.env.RECAP_FLOW_MIN_SCORE || 70);
const FLOW_MIN_PREMIUM = Number(process.env.RECAP_FLOW_MIN_PREMIUM || (IS_WEEKLY ? 150000 : 50000));
const FLOW_PAGES = IS_WEEKLY ? 5 : 3;   // pageSize 100 each
const FLOW_PAGE_SIZE = 100;

// A ticker needs at least this many independent source-legs to make the shortlist.
const MIN_LEGS = 2;

// Leg count is capped at this for RANKING. The scorecard (401 picks / 30 runs,
// 5-day forward) shows the hit-rate INVERTS past two legs: 2-leg 48% · 3-leg 26%
// · 4+-leg 17%. Extra legs mostly stack correlated mega-cap flow/fund noise rather
// than confirming a setup, so agreement beyond two is not evidence of a better
// trade. Legs still GATE the shortlist (MIN_LEGS); they just stop buying rank.
const LEG_RANK_CAP = 2;

// A name whose 60d close range is tighter than this is treated as dead — it can't
// produce a trade regardless of what the entry grade says. See the guard below.
const DEAD_RANGE_PCT = Number(process.env.RECAP_DEAD_RANGE || 0.05);

// "Affordable" cutoff for the dedicated under-$N section (lower-priced names).
const MAX_AFFORDABLE_PRICE = Number(process.env.RECAP_MAX_PRICE || 100);

// ---- helpers --------------------------------------------------------------
function findRepoRoot(start) {
  let dir = start;
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(dir, '.env_agent_api')) || existsSync(join(dir, 'CLAUDE.md'))) return dir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return resolve(SKILL_DIR, '../../..'); // best-effort
}

async function loadAgentKey() {
  if (process.env.AGENT_API_KEY) return process.env.AGENT_API_KEY.trim();
  const root = findRepoRoot(SKILL_DIR);
  const f = join(root, '.env_agent_api');
  if (existsSync(f)) {
    const raw = (await readFile(f, 'utf8')).trim();
    // file may be a bare token or KEY=value
    const m = raw.match(/^[A-Z_]+=(.*)$/);
    return (m ? m[1] : raw).trim();
  }
  return null;
}

// Dev-API key (X-API-Key td_live_*) for the NEW api.traderdaddy.pro plane.
async function loadDevKey() {
  if (process.env.TD_DEV_API_KEY) return process.env.TD_DEV_API_KEY.trim();
  const root = findRepoRoot(SKILL_DIR);
  const f = join(root, '.env_td_api');
  if (existsSync(f)) {
    const raw = (await readFile(f, 'utf8')).trim();
    const m = raw.match(/td_live_[A-Za-z0-9]+/);
    if (m) return m[0];
    const kv = raw.match(/^[A-Z_]+=(.*)$/);
    return (kv ? kv[1] : raw).trim();
  }
  return null;
}

// The Railway/edge WAF 403s requests carrying Node's default User-Agent, so we
// always present a browser-like UA. (curl works; bare `node-fetch` UA does not.)
const BASE_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
  Accept: 'application/json',
};

async function getJson(url, { headers = {}, label = url } = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { headers: { ...BASE_HEADERS, ...headers }, signal: ctrl.signal });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { data = null; }
    if (!res.ok) return { ok: false, status: res.status, error: (data && data.error) || text.slice(0, 200), data };
    return { ok: true, status: res.status, data };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? `timeout after ${TIMEOUT_MS}ms` : e.message };
  } finally {
    clearTimeout(t);
  }
}

async function pool(items, size, fn) {
  const out = new Array(items.length);
  let i = 0;
  async function worker() {
    while (i < items.length) {
      const idx = i++;
      out[idx] = await fn(items[idx], idx);
    }
  }
  await Promise.all(Array.from({ length: Math.min(size, items.length) }, worker));
  return out;
}

const sym = (r) => (r && (r.symbol || r.ticker || r.Symbol || r.Ticker) || '').toString().toUpperCase();
const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : (v == null ? null : Number(v)));
const fmt$ = (n) => {
  if (n == null || !Number.isFinite(n)) return '—';
  const a = Math.abs(n);
  if (a >= 1e9) return `${n < 0 ? '-' : ''}$${(a / 1e9).toFixed(1)}B`;
  if (a >= 1e6) return `${n < 0 ? '-' : ''}$${(a / 1e6).toFixed(1)}M`;
  if (a >= 1e3) return `${n < 0 ? '-' : ''}$${(a / 1e3).toFixed(0)}K`;
  return `${n < 0 ? '-' : ''}$${a.toFixed(0)}`;
};
const pct = (n) => (n == null || !Number.isFinite(n) ? '—' : `${n > 0 ? '+' : ''}${n.toFixed(1)}%`);
// a raw 0–1 fraction rendered as a percentage (hit-rates), no leading sign
const pctRaw = (n) => (n == null || !Number.isFinite(n) ? '—' : `${(n * 100).toFixed(0)}%`);
// weightDelta is a fraction (0.011 = +1.1%) from the per-ticker feeds, but an
// aggregate sum across funds in cross-fund convergence — show each correctly.
const wfmt = (v) => {
  if (v == null || !Number.isFinite(v)) return '';
  return Math.abs(v) < 1 ? pct(v * 100) : `Δ${v > 0 ? '+' : ''}${v.toFixed(2)} agg`;
};
const convStr = (v) => (v == null ? '' : (typeof v === 'number' ? v.toFixed(0) : String(v)));

// ---- StochK 40-line detector ---------------------------------------------
// Michael's earliest trigger: catch a name AS StochK breaks back up through 40
// after having dipped below it (a fresh momentum reclaim), not once it's already
// run to 85. Also flags the inverse — names that just DROPPED below 40 (were high,
// now pulling back) — for the Watch bucket. Both come from one StochK series
// computed off chart-data (screeners only give today's value, not the transition).
const STOCH_LINE = Number(process.env.RECAP_STOCH_LINE || 40);     // the reclaim line
const TURN_LOOKBACK = Number(process.env.RECAP_TURN_LOOKBACK || 2); // sessions since the cross to still count as "fresh"
const TURN_KMAX = Number(process.env.RECAP_TURN_KMAX || 68);        // above this K it's extended, not turning
// StochK(n) raw = (close-lowestLow)/(highestHigh-lowestLow); %K = SMA(raw, d).
function stochKSeries(rows, n = 14, d = 3) {
  const H = rows.map((r) => num(r.high)), L = rows.map((r) => num(r.low)), C = rows.map((r) => num(r.close));
  const raw = [];
  for (let i = 0; i < rows.length; i++) {
    if (i < n - 1) { raw.push(null); continue; }
    let hh = -Infinity, ll = Infinity;
    for (let j = i - n + 1; j <= i; j++) { if (H[j] > hh) hh = H[j]; if (L[j] < ll) ll = L[j]; }
    raw.push(hh === ll ? 50 : (100 * (C[i] - ll)) / (hh - ll));
  }
  const k = [];
  for (let i = 0; i < raw.length; i++) {
    if (i < n - 1 + d - 1) { k.push(null); continue; }
    let s = 0, c = 0;
    for (let j = i - d + 1; j <= i; j++) { if (raw[j] != null) { s += raw[j]; c++; } }
    k.push(c ? s / c : null);
  }
  return k;
}
// Classify the tail of a StochK series relative to the 40 line.
function classifyStoch(k) {
  const kk = k.filter((v) => v != null);
  if (kk.length < 3) return null;
  const kNow = kk[kk.length - 1];
  // most recent up-cross and down-cross through the line
  let upAgo = null, downAgo = null;
  for (let i = kk.length - 1; i >= 1; i--) {
    const cur = kk[i], prev = kk[i - 1];
    const ago = kk.length - 1 - i;
    if (upAgo == null && prev < STOCH_LINE && cur >= STOCH_LINE) upAgo = ago;
    if (downAgo == null && prev >= STOCH_LINE && cur < STOCH_LINE) downAgo = ago;
    if (upAgo != null && downAgo != null) break;
  }
  const turningUp = upAgo != null && upAgo <= TURN_LOOKBACK && kNow >= STOCH_LINE && kNow <= TURN_KMAX;
  const droppedBelow = kNow < STOCH_LINE && downAgo != null && (upAgo == null || downAgo < upAgo);
  return { kNow, upAgo, downAgo, turningUp, droppedBelow };
}

// ---- timestamp / output dir ----------------------------------------------
const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}`;
const OUT_DIR = join(SKILL_DIR, 'runs', stamp);
const RAW_DIR = join(OUT_DIR, 'raw');

async function saveRaw(name, obj) {
  await writeFile(join(RAW_DIR, `${name}.json`), JSON.stringify(obj, null, 2));
}

// ---- persistent cross-run watch store -------------------------------------
// A name that drops below the 40 line gets remembered across runs so we catch
// its reclaim even after it falls off every screener (the whole reason FIG-class
// names slip through: they leave the pullback screeners while still coiling). A
// name graduates the instant StochK crosses back above 40 (→ 🌅 Turning Up); it
// ages out if it coils past MAX_WATCH_DAYS without reclaiming (setup went stale).
const WATCH_STORE_PATH = join(SKILL_DIR, 'runs', '_watchlist.json');
const MAX_WATCH_DAYS = Number(process.env.RECAP_WATCH_MAX_DAYS || 21);
const todayISO = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
const daysBetween = (a, b) => Math.round((new Date(b) - new Date(a)) / 86400000);

async function loadWatchStore() {
  try {
    if (existsSync(WATCH_STORE_PATH)) {
      const s = JSON.parse(await readFile(WATCH_STORE_PATH, 'utf8'));
      if (s && s.names && typeof s.names === 'object') return s;
    }
  } catch { /* corrupt / missing → start fresh */ }
  return { version: 1, updated: null, names: {} };
}
async function saveWatchStore(store) {
  store.updated = todayISO;
  await writeFile(WATCH_STORE_PATH, JSON.stringify(store, null, 2));
}
// entries: [{ ticker, cls, price, sources, isPullback, onScreener }]
// Mutates store.names. Returns { graduated, aged } for the report.
function reconcileWatchStore(store, entries) {
  const graduated = [];
  const seen = new Set();
  for (const e of entries) {
    if (!e.cls) continue;
    seen.add(e.ticker);
    const rec = store.names[e.ticker];
    const reclaimed = e.cls.kNow >= STOCH_LINE && !e.cls.droppedBelow;
    if (rec && reclaimed) {
      // crossed back up through 40 → it graduated; hand it to the report and drop it
      const changePct = (rec.startPrice && e.price) ? ((e.price - rec.startPrice) / rec.startPrice * 100) : null;
      graduated.push({
        ticker: e.ticker, startPrice: rec.startPrice, price: e.price ?? rec.lastPrice, changePct,
        daysTracked: rec.firstTracked ? daysBetween(rec.firstTracked, todayISO) : 0,
        k: Math.round(e.cls.kNow), fresh: !!e.cls.turningUp, sources: rec.sources || e.sources || [],
      });
      delete store.names[e.ticker];
      continue;
    }
    if (e.cls.droppedBelow) {
      if (rec) {
        rec.lastSeen = todayISO; rec.lastPrice = e.price ?? rec.lastPrice;
        rec.lastK = Math.round(e.cls.kNow); rec.seenCount = (rec.seenCount || 1) + 1;
        rec.onScreener = e.onScreener; if (e.sources?.length) rec.sources = e.sources;
      } else if (e.isPullback) {
        // only pullback names EARN a new watch slot (keeps the store tight)
        store.names[e.ticker] = {
          firstTracked: todayISO, lastSeen: todayISO,
          startPrice: e.price ?? null, lastPrice: e.price ?? null,
          lastK: Math.round(e.cls.kNow), seenCount: 1,
          onScreener: e.onScreener, sources: e.sources || [],
        };
      }
    }
  }
  const aged = [];
  for (const [t, rec] of Object.entries(store.names)) {
    const age = rec.firstTracked ? daysBetween(rec.firstTracked, todayISO) : 0;
    if (age > MAX_WATCH_DAYS) { aged.push({ ticker: t, daysTracked: age }); delete store.names[t]; }
    else if (!seen.has(t)) rec.onScreener = false; // couldn't fetch/no-cross this run; keep tracking
  }
  return { graduated, aged };
}

// ---------------------------------------------------------------------------
async function main() {
  await mkdir(RAW_DIR, { recursive: true });
  const AGENT_KEY = await loadAgentKey();
  const authHeaders = AGENT_KEY ? { Authorization: `Bearer ${AGENT_KEY}` } : {};
  const health = {}; // leg -> status string

  // candidate registry: TICKER -> { legs:Set, screeners:[], tech:{}, flow:{}, inst:{}, cboe:false, reversal:{} }
  const reg = new Map();
  const cand = (t) => {
    if (!reg.has(t)) reg.set(t, { ticker: t, legs: new Set(), screeners: [], tech: null, flow: null, inst: null, cboe: false, reversal: null, watch: null, earnings: null });
    return reg.get(t);
  };

  // === 1. SCREENERS ========================================================
  const list = await getJson(`${TD_BASE}/api/screeners`);
  let screenerIds = [];
  if (list.ok && list.data && Array.isArray(list.data.screeners)) {
    screenerIds = list.data.screeners.map((s) => ({ id: s.id, name: s.name }));
  } else {
    // fallback to known ids
    screenerIds = ['momentum', 'bullish-pullback', 'volatility-squeeze', 'small-cap', 'volatility-surge', 'gamma-scan', 'csp-wheel', 'leaps', 'leveraged', 'daily-cuts'].map((id) => ({ id, name: id }));
  }

  const screenerResults = {};
  await pool(screenerIds, SCREENER_CONCURRENCY, async ({ id, name }) => {
    const r = await getJson(`${TD_BASE}/api/screeners/${id}/run`);
    const rows = r.ok && r.data ? (r.data.results || r.data.data || []) : [];
    screenerResults[id] = { name, ok: r.ok, count: rows.length, error: r.error, rows };
    await saveRaw(`screener_${id}`, r.data ?? { error: r.error });
    if (!r.ok) return;
    for (const row of rows) {
      const t = sym(row);
      if (!t) continue;
      const c = cand(t);
      c.screeners.push({ id, name, grade: row.metrics?.entryGrade ?? null, score: row.metrics?.entryScore ?? null });
      c.legs.add('screener');
      // capture technicals (prefer momentum/bullish-pullback which carry the full stack)
      const m = row.metrics || {};
      const tech = {
        price: num(row.price), changePct: num(row.changePct),
        rsi: num(row.rsi), adx: num(row.adx), stochK: num(row.stochK), atr: num(row.atr),
        sector: m.sector ?? row.sector ?? null,
        entryGrade: m.entryGrade ?? null, entryScore: num(m.entryScore),
        stochCrossover: m.stochCrossover ?? null, rsiZone: m.rsiZone ?? null,
        pullbackDepth: m.pullbackDepth ?? null, trendStrength: m.trendStrength ?? null,
        relativeVolume: num(m.relativeVolume), priceVsEma21Pct: num(m.priceVsEma21Pct),
        perfWeekPct: num(m.perfWeekPct), perfMonthPct: num(m.perfMonthPct),
        src: id,
      };
      const isPullback = id === 'momentum' || id === 'bullish-pullback';
      if (!c.tech || (isPullback && c.tech.src !== 'momentum' && c.tech.src !== 'bullish-pullback') ||
          (c.tech.rsi == null && tech.rsi != null)) {
        c.tech = tech;
      }
      // momentum-pullback RECOVERY detection (the user's edge):
      // not "buried in the pullback" (deep-oversold in a downtrend) but
      // ACTUALLY RECOVERING — RSI reclaimed bullish, price back above the 21EMA,
      // week no longer bleeding. Ghost Flow grades the buried ones SHORT even when
      // stoch is crossing up out of oversold; those are bounce candidates, not our
      // long setup. Require evidence the turn has already begun.
      if (isPullback) {
        const cross = (m.stochCrossover || '').toLowerCase() === 'yes';
        const sk = num(row.stochK);
        const rsiVal = num(row.rsi);
        const grade = (m.entryGrade || '').toUpperCase();
        const goodGrade = /A|B/.test(grade.replace(/[^A-Z]/g, ''));
        const rsiBull = /bull/i.test(m.rsiZone || '') || (rsiVal != null && rsiVal >= 50);
        const emaPct = num(m.priceVsEma21Pct);
        const reclaimedEma = emaPct != null && emaPct >= 0;           // back at/above the 21EMA — not buried under it
        const weekPct = num(m.perfWeekPct);
        const weekTurning = weekPct == null || weekPct >= 0;          // tape confirms — not still bleeding on the week
        const momentumUp = cross || (sk != null && sk >= 45);         // fresh cross OR stoch already climbing through the midline
        const recovering = goodGrade && rsiBull && reclaimedEma && weekTurning && momentumUp;
        if (recovering || cross) {
          c.reversal = {
            reversing: recovering, crossover: cross, stochK: sk, rsi: rsiVal, rsiZone: m.rsiZone ?? null,
            grade: m.entryGrade ?? null, entryScore: num(m.entryScore),
            pullbackDepth: m.pullbackDepth ?? null, priceVsEma21Pct: emaPct,
            perfWeekPct: weekPct, reclaimedEma,
          };
        }
      }
    }
  });
  const screenerOk = Object.values(screenerResults).filter((s) => s.ok).length;
  health.screeners = `${screenerOk}/${screenerIds.length} ran`;

  // === 1b. STOCH 40-LINE (turning up / dropped below) =====================
  // Scan the FULL screener union (not just pullback names) so we catch a fresh
  // <40→≥40 StochK reclaim on ANY name TD is surfacing — that's how we catch a
  // FIG-class recovery AT the cross (FIG sat in csp-wheel from 2026-06-27, three
  // days before its 06-30 reclaim; scanning only the pullback screeners missed it).
  // Each name gets one chart-data pull; best-effort, degrades to no-op on failure.
  const stochScanCands = [...reg.values()].filter((c) => (c.screeners || []).length > 0);
  let stochOk = 0;
  await pool(stochScanCands, 6, async (c) => {
    const r = await getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(c.ticker)}/chart-data?days=60`,
      { headers: authHeaders, label: `chart:${c.ticker}` });
    const rows = r.ok && r.data ? (r.data.chartData || r.data.data || []) : null;
    if (!rows || rows.length < 20) return;
    const clean = rows.filter((x) => x && x.close != null);
    const cls = classifyStoch(stochKSeries(clean));
    if (!cls) return;
    stochOk++;
    // tag pullback-screener membership: the Watch bucket stays scoped to those so
    // it doesn't balloon to a 100-name list over the full union.
    c.isPullbackName = (c.screeners || []).some((s) => s.id === 'momentum' || s.id === 'bullish-pullback');
    c.stoch40 = cls;
    c._lastClose = num(clean[clean.length - 1]?.close);
    // Dead-ticker guard: a name that barely moves games the entry-grade math (TALK
    // on 2026-08-02 ranged $5.12–$5.24 over 90d — 2% — and scored 🎯 A+ / entry 95).
    // There is no trade in a flatline, whatever the grade says.
    const cl = clean.map((x) => num(x.close)).filter((v) => v != null && v > 0);
    if (cl.length) {
      const lo = Math.min(...cl), hi = Math.max(...cl);
      c.range60 = (hi - lo) / lo;
      c.dead = c.range60 < DEAD_RANGE_PCT;
    }
    // enrich the reversal record so downstream tiers can read it
    if (cls.turningUp || cls.droppedBelow) {
      c.reversal = { ...(c.reversal || {}), stoch40: cls };
    }
  });
  health.stoch40 = `${stochOk}/${stochScanCands.length} charted`;

  // === 1c. PERSISTENT WATCH (cross-run) ===================================
  // Remember every name that dropped below 40 so we catch its reclaim on a later
  // run — even after it's fallen off all screeners. Store-only names get their own
  // chart pull here; on-screener names reuse the scan above.
  const watchStore = await loadWatchStore();
  const scannedSet = new Set(stochScanCands.map((c) => c.ticker));
  const watchEntries = stochScanCands
    .filter((c) => c.stoch40)
    .map((c) => ({
      ticker: c.ticker, cls: c.stoch40, price: c._lastClose ?? c.tech?.price ?? null,
      sources: (c.screeners || []).map((s) => s.id), isPullback: !!c.isPullbackName, onScreener: true,
    }));
  const storeOnly = Object.keys(watchStore.names).filter((t) => !scannedSet.has(t));
  let watchFetchOk = 0;
  await pool(storeOnly, 6, async (t) => {
    const r = await getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(t)}/chart-data?days=60`,
      { headers: authHeaders, label: `watch:${t}` });
    const rows = r.ok && r.data ? (r.data.chartData || r.data.data || []) : null;
    if (!rows || rows.length < 20) return;
    const clean = rows.filter((x) => x && x.close != null);
    const cls = classifyStoch(stochKSeries(clean));
    if (!cls) return;
    watchFetchOk++;
    watchEntries.push({
      ticker: t, cls, price: num(clean[clean.length - 1]?.close),
      sources: watchStore.names[t]?.sources || [], isPullback: false, onScreener: false,
    });
  });
  if (process.env.RECAP_DEBUG_WATCH) console.error(`[watch] storeOnly=${JSON.stringify(storeOnly)} fetched=${watchFetchOk} entries=${watchEntries.length}`);
  const { graduated, aged } = reconcileWatchStore(watchStore, watchEntries);
  await saveWatchStore(watchStore);
  health.watchStore = `${Object.keys(watchStore.names).length} tracked · ${graduated.length} graduated · ${aged.length} aged`;

  // === 2. FLOW (biggest flows + smart money) ===============================
  const flowAlerts = [];
  let flowAuthFail = false;
  for (let p = 1; p <= FLOW_PAGES; p++) {
    const r = await getJson(
      `${TD_BASE}/api/agent/unusual-activity?minScore=${FLOW_MIN_SCORE}&minPremium=${FLOW_MIN_PREMIUM}&timeFrame=${RECAP_WINDOW}&page=${p}&pageSize=${FLOW_PAGE_SIZE}`,
      { headers: authHeaders });
    if (!r.ok) { flowAuthFail = true; if (p === 1) await saveRaw('flow_error', { error: r.error, status: r.status }); break; }
    const rows = (r.data && r.data.data) || [];
    if (p === 1) await saveRaw('flow_page1', r.data);
    flowAlerts.push(...rows);
    if (rows.length < FLOW_PAGE_SIZE) break;
  }
  // repeats (institutional-conviction repeated strikes)
  const repeatsR = await getJson(`${TD_BASE}/api/unusual-activity/repeats?hours=24&limit=50`, { headers: authHeaders });
  const repeats = (repeatsR.ok && repeatsR.data && (repeatsR.data.repeatFlows || repeatsR.data.repeats)) || [];
  await saveRaw('flow_repeats', repeatsR.data ?? { error: repeatsR.error });

  // aggregate flow per ticker
  const flowAgg = new Map();
  for (const a of flowAlerts) {
    const t = sym(a); if (!t) continue;
    if (!flowAgg.has(t)) flowAgg.set(t, { ticker: t, bullPrem: 0, bearPrem: 0, count: 0, maxScore: 0, instAlpha: false, repeat: 0, topTradeType: null, topPrem: 0, conviction: null });
    const g = flowAgg.get(t);
    const prem = num(a.premium) || 0;
    const bull = /bull/i.test(a.sentiment || a.sentimentLabel || '');
    const bear = /bear/i.test(a.sentiment || a.sentimentLabel || '');
    if (bull) g.bullPrem += prem; else if (bear) g.bearPrem += prem;
    g.count++;
    g.maxScore = Math.max(g.maxScore, num(a.score) || 0);
    if (/institutional/i.test(a.tierDescription || '')) g.instAlpha = true;
    if (a.isRepeatFlow || (num(a.repeatCount) || 0) > 1) g.repeat = Math.max(g.repeat, num(a.repeatCount) || 1);
    if ((a.convictionLevel || '') && a.convictionLevel !== 'NORMAL') g.conviction = a.convictionLevel;
    if (prem > g.topPrem) { g.topPrem = prem; g.topTradeType = `${a.type} ${a.strike ?? ''} ${a.tradeType ?? ''}`.trim(); }
  }
  for (const [t, g] of flowAgg) {
    g.net = g.bullPrem - g.bearPrem;
    g.dir = g.net > 0 ? 'Bullish' : (g.net < 0 ? 'Bearish' : 'Mixed');
    const meaningful = Math.abs(g.net) >= FLOW_MIN_PREMIUM && g.maxScore >= FLOW_MIN_SCORE;
    const c = cand(t); c.flow = g;
    // Only BULLISH net flow is a convergence leg (this is a long-idea finder).
    // Meaningful bearish flow is tracked as a conflict, never as agreement.
    if (meaningful && g.net > 0) c.legs.add('flow_bull');
    if (meaningful && g.net < 0) c.flowBearish = true;
  }
  health.flow = flowAuthFail && flowAlerts.length === 0
    ? `FAILED (${AGENT_KEY ? 'key rejected' : 'no AGENT_API_KEY'})`
    : `${flowAlerts.length} alerts, ${flowAgg.size} tickers`;

  // === 3. NEW CBOE OPTION LISTINGS =========================================
  const cboeR = await getJson(`${TD_BASE}/api/options-listings`);
  await saveRaw('cboe_options_listings', cboeR.data ?? { error: cboeR.error });
  let newListings = [];
  if (cboeR.ok && cboeR.data && cboeR.data.latest) {
    const diff = cboeR.data.latest.diff || {};
    const opt = (diff.optionable && diff.optionable.new) || {};
    newListings = Object.keys(opt).map((k) => ({ symbol: k.toUpperCase(), name: opt[k] }));
    for (const l of newListings) { const c = cand(l.symbol); c.cboe = true; c.legs.add('cboe_new'); }
  }
  health.cboe = cboeR.ok ? `${newListings.length} new optionable` : `FAILED (${cboeR.error})`;

  // === 3b. COMMUNITY WATCHING (TD Pro — what users are piling into) =========
  // Replaces the retired Discord "👀 is watching" scraper: pulls the community
  // watchlist leaderboard straight from TD Pro. Graceful — if the endpoint
  // isn't deployed yet (404) this leg simply degrades and the run is unaffected.
  const watchR = await getJson(
    `${TD_BASE}/api/agent/community/watching?timeframe=24h&limit=20`,
    { headers: authHeaders });
  await saveRaw('community_watching', watchR.data ?? { error: watchR.error, status: watchR.status });
  let communityWatch = [];
  if (watchR.ok && watchR.data && Array.isArray(watchR.data.tickers)) {
    communityWatch = watchR.data.tickers.filter((w) => w && w.ticker);
    for (const w of communityWatch) {
      // only a net-positive crowd lean (more adds than removes) is a bullish leg
      if ((w.net ?? 0) > 0) {
        const c = cand(String(w.ticker).toUpperCase());
        c.watch = { watchers: w.watchers ?? 0, adds: w.adds ?? 0, removes: w.removes ?? 0, net: w.net ?? 0 };
        c.legs.add('community_watch');
      }
    }
  }
  health.communityWatch = watchR.ok
    ? `${communityWatch.length} watched`
    : (watchR.status === 404 ? 'endpoint not live yet (pending deploy)' : `FAILED (${watchR.error})`);

  // === 4. HEDGE FUNDS (TickerTrace 13F) ====================================
  const briefR = await getJson(`${TT_BASE}/briefing`);
  const instR = await getJson(`${TT_BASE}/institutional?limit=25`);
  const divR = await getJson(`${TT_BASE}/divergences`);
  await saveRaw('tickertrace_briefing', briefR.data ?? { error: briefR.error });
  await saveRaw('tickertrace_institutional', instR.data ?? { error: instR.error });
  await saveRaw('tickertrace_divergences', divR.data ?? { error: divR.error });

  const brief = briefR.ok ? briefR.data : {};
  const topBuys = brief.topBuys || [];
  const topSells = brief.topSells || [];
  const crossFund = brief.crossFundConvergence || [];
  const streaks = brief.activeStreaks || [];
  const instBuying = (instR.ok && instR.data && instR.data.buying) || [];
  const instSelling = (instR.ok && instR.data && instR.data.selling) || [];

  const attachInst = (rows, direction, leg) => {
    for (const r of rows) {
      const t = sym(r); if (!t) continue;
      const c = cand(t);
      c.inst = c.inst || {};
      c.inst.direction = direction;
      c.inst.weightDelta = num(r.weightDelta);
      c.inst.funds = num(r.funds ?? r.fundCount);
      c.inst.conviction = r.conviction ?? null;
      c.inst.sector = r.sector ?? c.inst.sector ?? null;
      if (leg) c.legs.add(leg);
    }
  };
  attachInst(topBuys, 'BUYING', 'inst_buy');
  attachInst(instBuying, 'BUYING', 'inst_buy');
  attachInst(crossFund.filter((r) => /buy/i.test(r.direction || '')), 'BUYING (cross-fund)', 'inst_crossfund');
  // sells: annotate as a conflict, never a bullish leg
  for (const r of [...topSells, ...instSelling]) {
    const t = sym(r); if (!t) continue;
    const c = cand(t);
    c.instSelling = true;
    if (!c.inst) { c.inst = { direction: 'SELLING', weightDelta: num(r.weightDelta), funds: num(r.funds ?? r.fundCount), sector: r.sector ?? null }; }
  }
  health.hedgeFunds = briefR.ok
    ? `${topBuys.length} top buys, ${crossFund.length} cross-fund, ${instBuying.length} buying`
    : `FAILED (${briefR.error})`;

  // === 4c. WEEK-AHEAD + REGIME (NEW dev API: earnings, econ, GEX, sectors) ==
  // A daily recap assumes "today is normal"; a Sunday-night weekly cannot — a
  // Thursday CPI or a Wednesday earnings print decides whether a coiled name is
  // a buy or a landmine. These legs come from the NEW dev plane (X-API-Key), are
  // all best-effort, and degrade gracefully (a bad key only dims these sections).
  const DEV_KEY = await loadDevKey();
  const devHeaders = DEV_KEY ? { 'X-API-Key': DEV_KEY } : {};
  const devGet = (path, label) => getJson(`${DEV_BASE}/${path}`, { headers: devHeaders, label: label || path });

  let earnings = [], econEvents = [], sectors = [], regime = null;
  if (!DEV_KEY) {
    health.weekAhead = 'no .env_td_api key — week-ahead/regime legs skipped';
  } else {
    // earnings reporting this week (landmines on the board)
    const er = await devGet('earnings?days=7');
    await saveRaw('dev_earnings', er.data ?? { error: er.error });
    if (er.ok && er.data && Array.isArray(er.data.events)) earnings = er.data.events;
    health.earnings = er.ok ? `${earnings.length} reporting this week` : `FAILED (${er.error})`;

    // economic catalyst calendar (next trading week)
    const ecr = await devGet('economic-calendar?week=next');
    await saveRaw('dev_econ_calendar', ecr.data ?? { error: ecr.error });
    if (ecr.ok && ecr.data && Array.isArray(ecr.data.events)) econEvents = ecr.data.events;
    health.econCalendar = ecr.ok ? `${econEvents.length} events` : `FAILED (${ecr.error})`;

    // regime: index put/call (market-stats) + SPY gamma (gex/SPY)
    const [msr, gxr] = await Promise.all([devGet('market-stats'), devGet('gex/SPY')]);
    await saveRaw('dev_market_stats', msr.data ?? { error: msr.error });
    await saveRaw('dev_gex_spy', gxr.data ?? { error: gxr.error });
    const gexData = gxr.ok && gxr.data ? (gxr.data.data || gxr.data) : null;
    regime = computeRegime(msr.ok ? msr.data : null, gexData);
    await saveRaw('regime', regime || { error: 'unavailable' });
    health.regime = regime ? `${regime.label} (score ${regime.score})` : 'unavailable';

    // sector tilt (which sectors money leaned into — colors the board)
    const scr = await devGet('sectors/flow');
    await saveRaw('dev_sector_flow', scr.data ?? { error: scr.error });
    const sd = scr.ok && scr.data ? (scr.data.data || scr.data) : null;
    if (sd && Array.isArray(sd.sectors)) sectors = sd.sectors;
    health.sectorFlow = scr.ok ? `${sectors.length} sectors` : `FAILED (${scr.error})`;
  }

  // tag any candidate reporting earnings this week (swing-entry landmine)
  const earningsBySym = new Map(earnings.map((e) => [sym(e), e]));
  const sectorPosture = buildSectorPosture(sectors);
  for (const c of reg.values()) {
    const e = earningsBySym.get(c.ticker);
    if (e) c.earnings = { date: e.date, day: e.dayOfWeek, time: e.time, epsEstimate: num(e.epsEstimate) };
  }

  // === 5. CONVERGENCE RANKING =============================================
  const BULLISH_LEGS = ['screener', 'flow_bull', 'inst_buy', 'inst_crossfund', 'cboe_new', 'community_watch'];
  const all = [...reg.values()].map((c) => {
    c.legCount = c.legs.size;
    const hasBullish = BULLISH_LEGS.some((l) => c.legs.has(l));
    // a name is conflicted when bullish sources disagree with bearish ones
    c.conflict = hasBullish && (c.flowBearish || c.instSelling);
    // only count aligned (bullish) flow magnitude toward the rank
    const alignedFlowMag = c.flow && c.flow.net > 0 ? c.flow.net : 0;
    const entry = c.tech?.entryScore || 0;
    const revBoost = c.reversal?.reversing ? 1 : 0;
    // Confirmed reversal outranks raw agreement: it's the only bucket that beats
    // the base rate (51% vs 47%), while leg count past LEG_RANK_CAP anti-correlates
    // with forward return. Rank on setup quality first, convergence second.
    const legTier = Math.min(c.legCount, LEG_RANK_CAP);
    c.rankScore = revBoost * 4e12 + legTier * 1e12 - (c.conflict ? 2.5e11 : 0) + alignedFlowMag + entry * 1e6;
    return c;
  });
  all.sort((a, b) => b.rankScore - a.rankScore);

  // In a risk-off / negative-gamma tape, demand one extra leg of agreement —
  // only the strongest convergence survives when the index backdrop fights longs.
  const effMinLegs = (regime && regime.label === 'RISK-OFF') ? MIN_LEGS + 1 : MIN_LEGS;
  let shortlist = all.filter((c) => c.legCount >= effMinLegs && !c.dead);
  if (shortlist.length < 8) {
    // backfill with single-leg high-quality (A/B grade screener OR confirmed reversal OR strong flow)
    const extra = all.filter((c) => c.legCount === 1 && !c.dead &&
      (c.reversal?.reversing || /A|B/.test((c.tech?.entryGrade || '').replace(/[^A-Z]/g, '')) || (c.flow && Math.abs(c.flow.net) >= 250000)));
    shortlist = [...shortlist, ...extra];
  }
  health.dead = `${all.filter((c) => c.dead).length} dead-range names filtered`;
  shortlist = shortlist.slice(0, SHORTLIST_SIZE);

  // reversal watch list (the edge) — momentum/bullish-pullback names turning up
  const reversalWatch = all
    .filter((c) => c.reversal && c.reversal.reversing && !c.dead)
    .sort((a, b) => (b.reversal.entryScore || 0) - (a.reversal.entryScore || 0));

  // 🌅 Turning Up — the EARLIEST catch: StochK just reclaimed the 40 line (fresh
  // <40→≥40 cross within TURN_LOOKBACK sessions, not yet extended). Michael's ideal
  // entry (FIG on 2026-06-30 at $18, before RSI/EMA confirmed).
  const turningUp = all
    .filter((c) => c.stoch40 && c.stoch40.turningUp && !c.dead)
    .sort((a, b) => (a.stoch40.upAgo ?? 9) - (b.stoch40.upAgo ?? 9) || (b.tech?.entryScore || 0) - (a.tech?.entryScore || 0));
  // 👁️ Watch (dropped below 40) — the PERSISTENT cross-run list. Names stay here
  // across runs (even after they leave every screener) until they reclaim 40
  // (→ graduated) or age out. Joined back to reg for live technicals when a name
  // is still on a screener this run.
  const watchList = Object.entries(watchStore.names).map(([t, rec]) => {
    const c = reg.get(t);
    return {
      ticker: t, price: rec.lastPrice, k: rec.lastK,
      daysTracked: rec.firstTracked ? daysBetween(rec.firstTracked, todayISO) : 0,
      droppedAgo: c?.stoch40?.downAgo ?? null,
      onScreener: !!rec.onScreener, sources: rec.sources || [],
      rsi: c?.tech?.rsi ?? null, emaPct: c?.tech?.priceVsEma21Pct ?? null,
    };
  }).sort((a, b) => (b.daysTracked - a.daysTracked) || ((a.k ?? 99) - (b.k ?? 99)));

  // === 5b. ENRICH technicals for shortlist names that arrived via flow/funds only
  const needEnrich = shortlist.filter((c) => !c.tech || c.tech.rsi == null);
  let enriched = 0;
  await pool(needEnrich, 4, async (c) => {
    const r = await getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(c.ticker)}`, { headers: authHeaders });
    if (!r.ok || !r.data) return;
    const tc = r.data.technicals || {};
    const op = r.data.options || {};
    const price = num(tc.close) ?? num(r.data.price);
    const ema21 = num(tc.ema21);
    const change = num(tc.change); // dollar change, not a percent
    const changePct = (change != null && price != null && (price - change) !== 0) ? (change / (price - change) * 100) : (c.tech?.changePct ?? null);
    c.tech = {
      ...(c.tech || {}),
      price: price ?? c.tech?.price ?? null,
      changePct,
      rsi: num(tc.rsi), adx: num(tc.adx),
      relativeVolume: num(tc.relVol),
      priceVsEma21Pct: (price != null && ema21) ? ((price - ema21) / ema21 * 100) : (c.tech?.priceVsEma21Pct ?? null),
      sector: c.tech?.sector ?? null,
      src: (c.tech?.src === 'momentum' || c.tech?.src === 'bullish-pullback') ? c.tech.src : 'ticker-api',
    };
    const em = op.expectedMove || {};
    c.optionsCtx = {
      callWall: num(op.callWall), putWall: num(op.putWall),
      expectedMovePct: num(em.percent), putCallOIRatio: num(op.putCallOIRatio), maxPain: num(op.maxPain),
    };
    enriched++;
  });
  health.enrich = `${enriched}/${needEnrich.length} flow/fund names enriched`;

  // affordable (sub-threshold price) convergence names — surfaced separately so
  // the recap isn't all $700+ mega-caps. `all` is already rankScore-sorted.
  const affordable = all
    .filter((c) => c.tech?.price != null && c.tech.price > 0 && c.tech.price <= MAX_AFFORDABLE_PRICE)
    .filter((c) => c.legCount >= 2 || c.reversal?.reversing || /A|B/.test((c.tech?.entryGrade || '').replace(/[^A-Z]/g, '')))
    .slice(0, 10);

  // NOTE: we deliberately don't render our own chart PNGs. The visual read lives
  // on Ghost Flow (TradingView) — it encodes the whole decision (grade / gate /
  // flow / squeeze / %R exhaust / vol premium / ATR risk / gamma walls), which a
  // bare candle+EMA render can't touch. The recap surfaces the data; the chart is
  // Ghost Flow. (scripts/render_chart.mjs renders the PNGs when you want them.)

  // pull the rolling track record if score_history.mjs has ever run
  let scorecard = null;
  try {
    const scPath = join(SKILL_DIR, 'runs', '_scorecard.json');
    if (existsSync(scPath)) scorecard = JSON.parse(await readFile(scPath, 'utf8'));
  } catch { /* best-effort */ }

  // earnings landmines that actually land on the shortlist
  const earningsOnBoard = shortlist.filter((c) => c.earnings).map((c) => ({ ticker: c.ticker, ...c.earnings }));

  // === 6. WRITE REPORT =====================================================
  const md = buildReport({
    stamp, now, TD_BASE, TT_BASE, health,
    flowAlerts, flowAgg, repeats, newListings,
    topBuys, topSells, crossFund, streaks, instBuying,
    screenerResults, shortlist, reversalWatch, turningUp, watchList, graduated, OUT_DIR, affordable,
    communityWatch,
    regime, econEvents, earnings, earningsOnBoard, sectorPosture, scorecard,
    isWeekly: IS_WEEKLY, effMinLegs,
  });
  const reportPath = join(OUT_DIR, 'report.md');
  await writeFile(reportPath, md);
  await saveRaw('shortlist', shortlist.map(serializeCand));
  await saveRaw('_health', health);

  // === 7. STDOUT recap =====================================================
  console.log(md);
  console.log(`\n──────────────────────────────────────────`);
  console.log(`📄 Report:   ${reportPath}`);
  console.log(`🗂  Raw JSON: ${RAW_DIR}`);
  console.log(JSON.stringify({ reportPath, rawDir: RAW_DIR, shortlist: shortlist.map((c) => c.ticker), health }, null, 0));
}

function serializeCand(c) {
  return { ticker: c.ticker, legs: [...c.legs], legCount: c.legCount, screeners: c.screeners, tech: c.tech, flow: c.flow, inst: c.inst, cboe: c.cboe, reversal: c.reversal, conflict: !!c.conflict, earnings: c.earnings };
}

// ---- regime gate ----------------------------------------------------------
// Blends index put/call (market-stats) + SPY net gamma (gex/SPY) into a single
// risk posture. Negative score = risk-off / fragile; positive = constructive.
function computeRegime(ms, gex) {
  if (!ms && !gex) return null;
  let score = 0;
  const notes = [];
  const r = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
  let pc = { spy: null, qqq: null, iwm: null };
  if (ms) {
    pc = { spy: r(ms.spy_put_call_ratio), qqq: r(ms.qqq_put_call_ratio), iwm: r(ms.iwm_put_call_ratio) };
    // higher put/call = more bearish positioning
    const contrib = (x) => (x == null ? 0 : (x >= 1.3 ? -20 : x >= 1.1 ? -10 : x <= 0.85 ? 15 : x <= 0.95 ? 8 : 0));
    score += contrib(pc.spy) + contrib(pc.qqq) + contrib(pc.iwm);
    const bearMajors = [pc.spy, pc.qqq, pc.iwm].filter((x) => x != null && x >= 1.1).length;
    if (bearMajors >= 2) notes.push(`${bearMajors}/3 index put/call bearish`);
    if (pc.iwm != null && pc.spy != null && pc.iwm - pc.spy > 0.4) notes.push('small-cap breadth weak (IWM put/call ≫ SPY)');
  }
  let gammaRegime = null, spotGEX = null, keyLevels = [];
  if (gex) {
    spotGEX = r(gex.totalGEX);
    gammaRegime = gex.interpretation?.marketRegime || null;
    keyLevels = gex.interpretation?.keyLevels || [];
    if (spotGEX != null) {
      if (spotGEX < 0) { score -= 15; notes.push('SPY negative gamma — dealers chase, moves amplify'); }
      else { score += 8; notes.push('SPY positive gamma — pinning / mean-reversion'); }
    }
  }
  let label, emoji, haircut;
  if (score <= -20) { label = 'RISK-OFF'; emoji = '🔴'; haircut = 0.55; }
  else if (score <= -5) { label = 'CAUTION'; emoji = '🟠'; haircut = 0.8; }
  else if (score >= 15) { label = 'RISK-ON'; emoji = '🟢'; haircut = 1.0; }
  else { label = 'NEUTRAL'; emoji = '🟡'; haircut = 0.95; }
  return {
    score, label, emoji, haircut, gammaRegime, pc, spotGEX, keyLevels, notes,
    largestTrade: ms ? { prem: num(ms.largest_trade_premium), sym: ms.largest_trade_symbol } : null,
    tradingDate: ms?.tradingDate ?? null, marketOpen: ms?.marketOpen ?? null,
  };
}

// One-line sector tilt: the few sectors with the strongest net-bullish flow lean.
function buildSectorPosture(sectors) {
  if (!sectors || !sectors.length) return null;
  const scored = sectors
    .map((s) => ({ sector: s.sector, etf: s.sectorETF, net: (num(s.bullishPremium) || 0) - (num(s.bearishPremium) || 0), senti: num(s.sentimentScore), chg: num(s.etfChangePct) }))
    .filter((s) => Number.isFinite(s.net));
  const lead = [...scored].sort((a, b) => b.net - a.net).slice(0, 3);
  const lag = [...scored].sort((a, b) => a.net - b.net).slice(0, 2);
  return { lead, lag };
}

// ---- report builder -------------------------------------------------------
function buildReport(ctx) {
  const { stamp, now, TD_BASE, TT_BASE, health, flowAgg, newListings,
    topBuys, topSells, crossFund, streaks, screenerResults, shortlist, reversalWatch,
    turningUp = [], watchList = [], graduated = [], affordable = [],
    communityWatch = [], regime = null, econEvents = [], earningsOnBoard = [], sectorPosture = null,
    scorecard = null, isWeekly = false } = ctx;
  const L = [];
  L.push(`# 📈 ${isWeekly ? 'Sunday Setup — Week Ahead' : 'Stock Recap'} — ${stamp.replace('_', ' ')}`);
  L.push('');
  L.push(`_Generated ${now.toString()}_`);
  L.push('');

  // ===== REGIME BANNER (how to trade this week) =====
  if (regime) {
    const p = regime.pc || {};
    const pcStr = `put/call — SPY ${p.spy != null ? p.spy.toFixed(2) : '—'} · QQQ ${p.qqq != null ? p.qqq.toFixed(2) : '—'} · IWM ${p.iwm != null ? p.iwm.toFixed(2) : '—'}`;
    L.push(`> ${regime.emoji} **Regime: ${regime.label}** (score ${regime.score})${regime.gammaRegime ? ` · ${regime.gammaRegime}` : ''}`);
    L.push(`> ${pcStr}${regime.spotGEX != null ? ` · SPY net-GEX ${fmt$(regime.spotGEX)}` : ''}`);
    if (regime.notes.length) L.push(`> ${regime.notes.join('. ')}.`);
    if (regime.label === 'RISK-OFF' || regime.label === 'CAUTION') L.push(`> **Longs on a short leash — convergence bar tightened this run.**`);
    if (regime.marketOpen === false) L.push(`> ⚠️ Market closed — flow leg reflects ${regime.tradingDate || 'last session'}, not live.`);
    L.push('');
  }

  // ===== TRACK RECORD (from score_history.mjs) =====
  if (scorecard && scorecard.overall) {
    const o = scorecard.overall;
    const rw = scorecard.buckets?.reversalWatch;
    L.push(`📋 **Track record** (last ${scorecard.runsScored || '—'} scored runs, ${scorecard.horizonDays || 5}-day forward): ` +
      `shortlist hit-rate **${pctRaw(o.hitRate)}**, median **${pct(o.medianFwdPct)}**` +
      (rw && rw.n ? ` · Reversal Watch hit-rate **${pctRaw(rw.hitRate)}**, median **${pct(rw.medianFwdPct)}**` : ''));
    L.push('');
  }

  // ===== WEEK AHEAD — macro clock + earnings landmines =====
  if (econEvents.length || earningsOnBoard.length || sectorPosture) {
    L.push('## 🗓️ The Week Ahead');
    L.push('');
    if (econEvents.length) {
      const impactEmoji = (i) => (/high/i.test(i) ? '🔴' : /med/i.test(i) ? '🟠' : '⚪');
      L.push(`| Day | Time | Event | Impact |`);
      L.push(`|---|---|---|---|`);
      for (const e of econEvents.slice(0, 12)) {
        const day = e.date ? new Date(e.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' }) : '—';
        L.push(`| ${day} ${e.date ? e.date.slice(5) : ''} | ${e.time || '—'} | ${e.event} | ${impactEmoji(e.impact)} ${e.impact || ''} |`);
      }
      const hinge = econEvents.find((e) => /high/i.test(e.impact || ''));
      if (hinge) L.push(`\n**Hinge event:** ${hinge.event} (${hinge.date}) — size light into it.`);
      L.push('');
    }
    if (earningsOnBoard.length) {
      L.push(`**⚠️ Earnings on the board this week** (a swing entry into a print is a coin-flip, not a setup):`);
      L.push('');
      L.push(earningsOnBoard.map((e) => `\`${e.ticker}\` ${e.day || ''} ${e.time || ''}`.trim()).join(' · '));
      L.push('');
    }
    if (sectorPosture && sectorPosture.lead?.length) {
      const fmtS = (s) => `${s.etf || s.sector} (${pct(s.chg)})`;
      L.push(`**Sector tilt:** money leaning into ${sectorPosture.lead.map(fmtS).join(', ')}` +
        (sectorPosture.lag?.length ? ` · leaning out of ${sectorPosture.lag.map(fmtS).join(', ')}` : '') + '.');
      L.push('');
    }
  }

  // data health
  L.push('**Data sources**');
  L.push('');
  L.push(`| Leg | Status |`);
  L.push(`|---|---|`);
  L.push(`| Screeners (TD Pro) | ${health.screeners || '—'} |`);
  L.push(`| Options flow (TD Pro agent) | ${health.flow || '—'} |`);
  L.push(`| New CBOE listings (TD Pro) | ${health.cboe || '—'} |`);
  L.push(`| Community watching (TD Pro) | ${health.communityWatch || '—'} |`);
  L.push(`| Hedge funds / 13F (TickerTrace) | ${health.hedgeFunds || '—'} |`);
  if (health.weekAhead) {
    L.push(`| Week-ahead / regime (dev API) | ${health.weekAhead} |`);
  } else {
    L.push(`| Earnings calendar (dev API) | ${health.earnings || '—'} |`);
    L.push(`| Economic calendar (dev API) | ${health.econCalendar || '—'} |`);
    L.push(`| Regime gate (mkt-stats + SPY GEX) | ${health.regime || '—'} |`);
    L.push(`| Sector flow (dev API) | ${health.sectorFlow || '—'} |`);
  }
  L.push(`| Technicals enrichment | ${health.enrich || '—'} |`);
  L.push('');

  // ===== RECAP =====
  L.push('## 📊 Market Recap');
  L.push('');

  // flow
  const flows = [...flowAgg.values()].sort((a, b) => Math.abs(b.net) - Math.abs(a.net));
  const totBull = flows.reduce((s, f) => s + f.bullPrem, 0);
  const totBear = flows.reduce((s, f) => s + f.bearPrem, 0);
  L.push('### 💰 Options flow (biggest premium today)');
  L.push('');
  L.push(`Total bullish premium **${fmt$(totBull)}** vs bearish **${fmt$(totBear)}** across tracked alerts.`);
  L.push('');
  if (flows.length) {
    L.push(`| Ticker | Net flow | Dir | Top trade | Score | Inst-α | Repeat |`);
    L.push(`|---|---|---|---|---|---|---|`);
    for (const f of flows.slice(0, 10)) {
      L.push(`| **${f.ticker}** | ${fmt$(f.net)} | ${f.dir} | ${f.topTradeType || '—'} | ${f.maxScore} | ${f.instAlpha ? '🛡️' : ''} | ${f.repeat > 1 ? '🔁×' + f.repeat : ''} |`);
    }
  } else {
    L.push('_No qualifying flow (quiet tape or flow leg unavailable)._');
  }
  L.push('');

  // hedge funds
  L.push('### 🏛️ Hedge funds (13F — TickerTrace)');
  L.push('');
  if (topBuys.length || crossFund.length) {
    if (crossFund.length) {
      L.push(`**Cross-fund convergence** (multiple funds into the same name — strongest signal):`);
      L.push(crossFund.slice(0, 6).map((r) => `\`${sym(r)}\` (${r.funds ?? r.providers ?? '?'} funds${/sell/i.test(r.direction || '') ? ', selling' : ', buying'})`).join(' · '));
      L.push('');
    }
    L.push(`**Top buys:** ` + (topBuys.slice(0, 6).map((r) => `\`${sym(r)}\``).join(' · ') || '—'));
    L.push('');
    L.push(`**Top sells:** ` + (topSells.slice(0, 6).map((r) => `\`${sym(r)}\``).join(' · ') || '—'));
    L.push('');
    if (streaks.length) {
      L.push(`**Hot streaks:** ` + streaks.slice(0, 6).map((s) => `${sym(s)} (${s.fund}, ${s.days}d ${s.direction})`).join(' · '));
      L.push('');
    }
  } else {
    L.push('_Hedge-fund leg unavailable._');
    L.push('');
  }

  // community watching (TD Pro members)
  L.push('### 👀 What TD Pro people are watching');
  L.push('');
  if (communityWatch && communityWatch.length) {
    const top = communityWatch.slice(0, 12);
    L.push('_Tickers TD Pro members are piling into (net watchlist adds, last 24h). Net-positive names count as a bullish convergence leg._');
    L.push('');
    L.push(top.map((w) => `\`${w.ticker}\` (+${w.net}${w.watchers ? `, ${w.watchers} ppl` : ''})`).join(' · '));
    L.push('');
  } else {
    const why = (health.communityWatch || '').includes('not live')
      ? '_Community-watch endpoint not deployed yet — leg pending (will light up after the TD Pro deploy)._'
      : '_No community-watch data this run._';
    L.push(why);
    L.push('');
  }

  // CBOE
  L.push('### 🆕 New CBOE optionable listings');
  L.push('');
  if (newListings.length) {
    L.push(newListings.slice(0, 25).map((l) => `\`${l.symbol}\``).join(' · '));
    if (newListings.length > 25) L.push(`\n…and ${newListings.length - 25} more.`);
  } else {
    L.push('_None new in latest scan._');
  }
  L.push('');

  // screener hit counts
  L.push('### 🔎 Screener hits');
  L.push('');
  L.push(`| Screener | Hits |`);
  L.push(`|---|---|`);
  for (const [id, s] of Object.entries(screenerResults)) {
    L.push(`| ${s.name || id} | ${s.ok ? s.count : '⚠️ ' + (s.error || 'failed')} |`);
  }
  L.push('');

  // ===== SHORTLIST =====
  L.push('## 🎯 Shortlist — convergence ranked');
  L.push('');
  L.push(`_Ranked by how many independent sources point at the same ticker. ${shortlist.length} names._`);
  L.push('');
  if (shortlist.length) {
    L.push(`| # | Ticker | Legs | Sources | Price | Tech (RSI/ADX/Stoch) | Grade | Flow | Hedge funds | Edge |`);
    L.push(`|---|---|---|---|---|---|---|---|---|---|`);
    shortlist.forEach((c, i) => {
      const t = c.tech || {};
      const sources = legLabels(c);
      const tech = `${t.rsi != null ? t.rsi.toFixed(0) : '—'}/${t.adx != null ? t.adx.toFixed(0) : '—'}/${t.stochK != null ? t.stochK.toFixed(0) : '—'}`;
      const flow = c.flow && Math.abs(c.flow.net) >= 1 ? `${fmt$(c.flow.net)} ${c.flow.dir}${c.flow.instAlpha ? ' 🛡️' : ''}` : '—';
      const inst = c.inst ? `${c.inst.direction}${c.inst.funds ? ' (' + c.inst.funds + ')' : ''}` : '—';
      const edge = [c.reversal?.reversing ? '🔄 recovering' : '', c.earnings ? `⚠️ ER ${c.earnings.day || c.earnings.date || ''}`.trim() : '', c.conflict ? '⚠️ conflict' : ''].filter(Boolean).join(' ');
      L.push(`| ${i + 1} | **${c.ticker}** | ${c.legCount} | ${sources} | ${t.price != null ? '$' + t.price.toFixed(2) : '—'} | ${tech} | ${t.entryGrade || '—'} | ${flow} | ${inst} | ${edge} |`);
    });
  } else {
    L.push('_No multi-source convergence found this run._');
  }
  L.push('');

  // per-pick detail for the top picks
  const detail = shortlist.slice(0, 8);
  if (detail.length) {
    L.push('### 🔬 Top picks — detail');
    L.push('');
    for (const c of detail) {
      const t = c.tech || {};
      L.push(`**${c.ticker}** — ${c.legCount} legs: ${legLabels(c)}`);
      const bits = [];
      if (t.price != null) bits.push(`price $${t.price.toFixed(2)} (${pct(t.changePct)})`);
      if (t.sector) bits.push(t.sector);
      if (t.rsi != null) bits.push(`RSI ${t.rsi.toFixed(0)}`);
      if (t.adx != null) bits.push(`ADX ${t.adx.toFixed(0)}`);
      if (t.stochK != null) bits.push(`StochK ${t.stochK.toFixed(0)}`);
      if (t.rsiZone) bits.push(`zone ${t.rsiZone}`);
      if (t.pullbackDepth) bits.push(`pullback ${t.pullbackDepth}`);
      if (t.entryGrade) bits.push(`grade ${t.entryGrade}`);
      if (t.perfWeekPct != null) bits.push(`1w ${pct(t.perfWeekPct)}`);
      if (bits.length) L.push('- ' + bits.join(' · '));
      if (c.screeners.length) L.push(`- Screeners: ${c.screeners.map((s) => s.name + (s.grade ? ` (${s.grade})` : '')).join(', ')}`);
      if (c.flow) L.push(`- Flow: net ${fmt$(c.flow.net)} ${c.flow.dir}, ${c.flow.count} alerts, max score ${c.flow.maxScore}${c.flow.instAlpha ? ', 🛡️ institutional-alpha tier' : ''}${c.flow.repeat > 1 ? `, 🔁 repeat ×${c.flow.repeat}` : ''}`);
      if (c.inst) { const w = wfmt(c.inst.weightDelta); const cv = convStr(c.inst.conviction); L.push(`- Hedge funds: ${c.inst.direction}${c.inst.funds ? `, ${c.inst.funds} funds` : ''}${w ? `, ${w}` : ''}${cv ? `, conviction ${cv}` : ''}`); }
      if (c.optionsCtx) { const o = c.optionsCtx; const ob = []; if (o.callWall != null) ob.push(`call wall ${o.callWall}`); if (o.putWall != null) ob.push(`put wall ${o.putWall}`); if (o.expectedMovePct != null) ob.push(`exp move ±${o.expectedMovePct.toFixed(1)}%`); if (o.putCallOIRatio != null) ob.push(`P/C OI ${o.putCallOIRatio.toFixed(2)}`); if (ob.length) L.push(`- Options: ${ob.join(' · ')}`); }
      if (c.cboe) L.push(`- 🆕 Newly optionable on CBOE`);
      if (c.conflict) L.push(`- ⚠️ **Conflict:** bullish source(s) disagree with ${c.flowBearish ? 'bearish options flow' : ''}${c.flowBearish && c.instSelling ? ' and ' : ''}${c.instSelling ? 'fund selling' : ''} — confirm before sizing.`);
      if (c.reversal?.reversing) L.push(`- 🔄 **Recovering out of the pullback** — reclaimed 21EMA (${c.reversal.priceVsEma21Pct != null ? pct(c.reversal.priceVsEma21Pct) : '—'}), RSI ${c.reversal.rsi != null ? c.reversal.rsi.toFixed(0) : '—'} ${c.reversal.rsiZone || ''}, week ${c.reversal.perfWeekPct != null ? pct(c.reversal.perfWeekPct) : '—'}, StochK ${c.reversal.stochK?.toFixed(0)}, ${c.reversal.grade || ''}`);
      if (c.earnings) L.push(`- ⚠️ **Earnings ${c.earnings.day || ''} ${c.earnings.time || ''} (${c.earnings.date || ''})** — a swing entry into a print is a coin-flip, not a setup. Trade it after, or size for the gap.`);
      L.push(`- 📈 Confirm the visual on **Ghost Flow** (grade / gate / flow / squeeze / gamma walls).`);
      L.push('');
    }
  }

  // ===== AFFORDABLE (under threshold) =====
  L.push(`## 💵 Under $${MAX_AFFORDABLE_PRICE} — affordable picks`);
  L.push('');
  L.push(`_Same convergence logic, filtered to names trading at or below $${MAX_AFFORDABLE_PRICE} so the list isn't all mega-caps._`);
  L.push('');
  if (affordable.length) {
    L.push(`| Ticker | Price | Legs | Sources | Tech (RSI/ADX/Stoch) | Grade | Flow | Hedge funds | Edge |`);
    L.push(`|---|---|---|---|---|---|---|---|---|`);
    for (const c of affordable) {
      const t = c.tech || {};
      const tech = `${t.rsi != null ? t.rsi.toFixed(0) : '—'}/${t.adx != null ? t.adx.toFixed(0) : '—'}/${t.stochK != null ? t.stochK.toFixed(0) : '—'}`;
      const flow = c.flow && Math.abs(c.flow.net) >= 1 ? `${fmt$(c.flow.net)} ${c.flow.dir}` : '—';
      const inst = c.inst ? `${c.inst.direction}${c.inst.funds ? ' (' + c.inst.funds + ')' : ''}` : '—';
      const edge = [c.reversal?.reversing ? '🔄 recovering' : '', c.conflict ? '⚠️ conflict' : ''].filter(Boolean).join(' ');
      L.push(`| **${c.ticker}** | $${t.price.toFixed(2)} | ${c.legCount} | ${legLabels(c)} | ${tech} | ${t.entryGrade || '—'} | ${flow} | ${inst} | ${edge} |`);
    }
  } else {
    L.push(`_No qualifying names under $${MAX_AFFORDABLE_PRICE} this run._`);
  }
  L.push('');

  // ===== RECOVERY WATCH (the edge) =====
  // ===== TURNING UP (earliest catch — 40-line reclaim) =====
  L.push('## 🌅 Turning Up — StochK reclaimed the 40 line');
  L.push('');
  L.push('_The **earliest** catch, scanned across **every** screener (not just pullback): StochK just crossed back **up through 40** after dipping below it — the moment the turn starts, before RSI/EMA confirm (FIG on 2026-06-30 at $18 was this, then +32%). Fresh cross within 2 sessions, K not yet extended (≤68)._');
  L.push('');
  if (turningUp.length) {
    L.push(`| Ticker | Price | K now | Crossed | Source | Grade | RSI | vs EMA21 | Flow | Fund |`);
    L.push(`|---|---|---|---|---|---|---|---|---|---|`);
    for (const c of turningUp.slice(0, 20)) {
      const s = c.stoch40, t = c.tech || {};
      const ago = s.upAgo === 0 ? 'today' : `${s.upAgo}d ago`;
      const src = (c.screeners || []).map((x) => x.id).join(', ') || '—';
      const flowC = c.flow && c.flow.net > 0 ? `${fmt$(c.flow.net)} 🟢` : (c.flow && c.flow.net < 0 ? `${fmt$(c.flow.net)} 🔴` : '—');
      const fundC = c.inst && /BUY/i.test(c.inst.direction) ? `BUYING ✅` : (c.inst ? c.inst.direction : '—');
      L.push(`| **${c.ticker}** | ${t.price != null ? '$' + t.price.toFixed(2) : '—'} | ${s.kNow.toFixed(0)} | ${ago} | ${src} | ${t.entryGrade || '—'} | ${t.rsi != null ? t.rsi.toFixed(0) : '—'} | ${t.priceVsEma21Pct != null ? pct(t.priceVsEma21Pct) : '—'} | ${flowC} | ${fundC} |`);
    }
    L.push('');
    L.push('> Scanned across **all** screeners, not just pullback — this is how we catch a FIG-class name at the cross (FIG sat in csp-wheel before its 06-30 reclaim). Fires earlier than Recovery Watch (which waits for the full RSI+EMA reclaim): earlier = better price, but noisier — confirm the turn on **Ghost Flow** (W-GATE, FLOW positive, bouncing not rolling) before sizing.');
  } else {
    L.push('_No screener names reclaimed the 40 line in the last 2 sessions this run._');
  }
  L.push('');

  // ===== GRADUATED (a tracked Watch name just reclaimed 40) =====
  if (graduated.length) {
    L.push('## 🎓 Graduated from Watch — reclaimed 40 this run');
    L.push('');
    L.push('_These sat on the persistent 👁️ Watch list (they\'d dropped below 40 on a prior run) and just **crossed back up through 40** — the payoff of tracking them across runs, even after they fell off every screener. This is exactly the FIG catch: watch the drop, own the reclaim._');
    L.push('');
    L.push(`| Ticker | Reclaim K | Was | Now | Since watch | Days tracked | Prior source |`);
    L.push(`|---|---|---|---|---|---|---|`);
    for (const g of graduated.slice(0, 20)) {
      const src = (g.sources || []).join(', ') || '—';
      const fresh = g.fresh ? ' 🔥' : '';
      L.push(`| **${g.ticker}**${fresh} | ${g.k} | ${g.startPrice != null ? '$' + g.startPrice.toFixed(2) : '—'} | ${g.price != null ? '$' + g.price.toFixed(2) : '—'} | ${g.changePct != null ? pct(g.changePct) : '—'} | ${g.daysTracked}d | ${src} |`);
    }
    L.push('');
    L.push('> 🔥 = fresh cross (within the last 2 sessions — the ideal entry). Confirm on **Ghost Flow** before sizing; a reclaim in a RISK-OFF tape can still roll back over.');
    L.push('');
  }

  L.push('## 🔄 Momentum Pullback — Recovery Watch');
  L.push('');
  L.push('_Confirmed tier: pullback names that are **already recovering** — RSI reclaimed bullish (≥50), price back above the 21EMA, week no longer bleeding, A/B grade. Not the still-buried, deep-oversold names (those grade SHORT on Ghost Flow — bounce candidates, not longs)._');
  L.push('');
  if (reversalWatch.length) {
    L.push(`| Ticker | RSI | vs EMA21 | Week | StochK | Grade | Entry | Pullback | Flow confirm | Fund confirm |`);
    L.push(`|---|---|---|---|---|---|---|---|---|---|`);
    for (const c of reversalWatch.slice(0, 20)) {
      const r = c.reversal;
      const flowC = c.flow && c.flow.net > 0 ? `${fmt$(c.flow.net)} 🟢` : (c.flow && c.flow.net < 0 ? `${fmt$(c.flow.net)} 🔴` : '—');
      const fundC = c.inst && /BUY/i.test(c.inst.direction) ? `BUYING ✅` : (c.inst ? c.inst.direction : '—');
      L.push(`| **${c.ticker}** | ${r.rsi != null ? r.rsi.toFixed(0) : '—'} ${r.rsiZone || ''} | ${r.priceVsEma21Pct != null ? pct(r.priceVsEma21Pct) : '—'} | ${r.perfWeekPct != null ? pct(r.perfWeekPct) : '—'} | ${r.stochK != null ? r.stochK.toFixed(0) : '—'} | ${r.grade || '—'} | ${r.entryScore != null ? r.entryScore.toFixed(0) : '—'} | ${r.pullbackDepth || '—'} | ${flowC} | ${fundC} |`);
    }
    L.push('');
    L.push('> Names with **both** a 🟢 flow confirm and a fund ✅ are the highest-conviction recoveries — your setup with smart money already leaning in.');
  } else {
    L.push('_No pullback names have reclaimed (RSI back bullish + above the 21EMA) this run — everything flagged is still buried. Nothing to chase._');
  }
  L.push('');

  // ===== WATCH (persistent cross-run list of names below 40) =====
  L.push('## 👁️ Watch — persistent, tracked until they reclaim 40');
  L.push('');
  L.push('_The **cross-run** watch list. A name lands here when it falls through 40 and **stays** across runs — even after it drops off every screener — until it reclaims 40 (→ 🎓 Graduated) or ages out (21 days coiling with no reclaim). This is how we never lose a FIG-class name between the drop and the turn. Not actionable while here; watch, don\'t buy. MIDD/CRS on 2026-07-19 were the archetype._');
  L.push('');
  if (watchList.length) {
    L.push(`| Ticker | Price | K now | Tracked | On screener | RSI | vs EMA21 | Source |`);
    L.push(`|---|---|---|---|---|---|---|---|`);
    for (const w of watchList.slice(0, 30)) {
      const onScr = w.onScreener ? 'yes' : 'off ✂️';
      const src = (w.sources || []).join(', ') || '—';
      L.push(`| **${w.ticker}** | ${w.price != null ? '$' + Number(w.price).toFixed(2) : '—'} | ${w.k != null ? w.k : '—'} | ${w.daysTracked}d | ${onScr} | ${w.rsi != null ? w.rsi.toFixed(0) : '—'} | ${w.emaPct != null ? pct(w.emaPct) : '—'} | ${src} |`);
    }
    L.push('');
    L.push('> `off ✂️` = no longer on any screener this run — we\'re still tracking it purely off StochK, which is the whole point. When one crosses back **up** through 40 it graduates to 🎓 above.');
  } else {
    L.push('_Watch list is empty — nothing is coiling below 40 right now._');
  }
  L.push('');

  // ===== VISUAL = GHOST FLOW =====
  L.push('## 📈 The visual lives on Ghost Flow');
  L.push('');
  L.push('_No chart PNGs in this run by design. Pull the names above up on **Ghost Flow** (TradingView) for the read — it encodes the whole decision (grade / W-gate / flow / squeeze / %R exhaust / vol premium / ADX-RSI / ATR risk + gamma walls) that a bare candle render can\'t. The tables here are the data; Ghost Flow is the picture._');
  L.push('');
  L.push('> ⚠️ **Ticker exchange:** every symbol here is US-listed (TD\'s universe). On TradingView make sure you\'re on the US exchange — some tickers collide with foreign listings. E.g. **AIR = NYSE:AIR (AAR Corp)**, not Euronext Paris Airbus SE. If a Ghost Flow read looks nothing like the price/RSI in the table, you\'re on the wrong exchange.');
  L.push('');
  L.push('---');
  L.push(`_Raw JSON snapshots saved alongside this report under \`raw/\`. Re-run the skill any time for a fresh pull._`);
  return L.join('\n');
}

function legLabels(c) {
  const map = { screener: 'screener', flow_bull: 'flow🟢', flow_bear: 'flow🔴', inst_buy: 'funds-buy', inst_crossfund: 'cross-fund', cboe_new: 'new-CBOE', community_watch: 'watching👀' };
  return [...c.legs].map((l) => map[l] || l).join(', ');
}

main().catch((e) => { console.error('gather.mjs fatal:', e); process.exit(1); });
