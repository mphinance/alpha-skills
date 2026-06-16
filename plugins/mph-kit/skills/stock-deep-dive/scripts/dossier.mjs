#!/usr/bin/env node
// stock-deep-dive / dossier.mjs
// The deepest single-stock pull we have: everything TraderDaddy Pro + TickerTrace
// know about ONE ticker, in one shot. Technicals, full options positioning,
// recent options flow, and 13F institutional ownership + recent fund changes.
// Renders a 90-day chart (reuses the stock-recap skill's venv + render_chart.py).
//
// Usage:  node dossier.mjs PLTR              (one ticker)
//         node dossier.mjs PLTR NVDA SOFI    (several — one dossier each)
//
// Auth: AGENT_API_KEY (read from repo-root .env_agent_api or env) for /api/agent/*.
// TickerTrace is public. Node 18+ (global fetch). No external deps.
//
// News is NOT pulled here (TD Pro has no news endpoint) — the skill instructs
// Claude to WebSearch for recent catalysts and fold them into the verdict.

import { writeFile, mkdir, readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');
// stock-recap lives next to us in the same .claude/skills dir — reuse its venv +
// chart renderer rather than installing a second matplotlib/pandas stack.
const RECAP_DIR = resolve(SKILL_DIR, '..', 'stock-recap');

const TD_BASE = process.env.TD_API_URL || 'https://traderdaddy-pro-whop-production.up.railway.app';
const TT_BASE = process.env.TICKERTRACE_API_URL || 'https://api.tickertrace.pro/api/v1';
const TIMEOUT_MS = Number(process.env.DD_TIMEOUT_MS || 45000);
const FLOW_TIMEFRAME = process.env.DD_FLOW_TIMEFRAME || 'week'; // today | week | month
const FLOW_PAGES = 2, FLOW_PAGE_SIZE = 100;

// ---- repo-root / key resolution (same pattern as stock-recap) --------------
function findRepoRoot(start) {
  let dir = start;
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(dir, '.env_agent_api')) || existsSync(join(dir, 'CLAUDE.md'))) return dir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return resolve(SKILL_DIR, '../../..');
}
async function loadAgentKey() {
  if (process.env.AGENT_API_KEY) return process.env.AGENT_API_KEY.trim();
  const f = join(findRepoRoot(SKILL_DIR), '.env_agent_api');
  if (existsSync(f)) {
    const raw = (await readFile(f, 'utf8')).trim();
    const m = raw.match(/^[A-Z_]+=(.*)$/);
    return (m ? m[1] : raw).trim();
  }
  return null;
}

// The Railway/edge WAF 403s the bare Node UA — always present a browser UA.
const BASE_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
  Accept: 'application/json',
};
async function getJson(url, headers = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { headers: { ...BASE_HEADERS, ...headers }, signal: ctrl.signal });
    const text = await res.text();
    let data; try { data = JSON.parse(text); } catch { data = null; }
    if (!res.ok) return { ok: false, status: res.status, error: (data && data.error) || text.slice(0, 160), data };
    return { ok: true, status: res.status, data };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? `timeout after ${TIMEOUT_MS}ms` : e.message };
  } finally { clearTimeout(t); }
}

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : (v == null ? null : (Number.isFinite(Number(v)) ? Number(v) : null)));
const f2 = (n) => (n == null ? '—' : Number(n).toFixed(2));
const f0 = (n) => (n == null ? '—' : Number(n).toFixed(0));
const pct = (n) => (n == null ? '—' : `${n > 0 ? '+' : ''}${Number(n).toFixed(1)}%`);
const fmt$ = (n) => {
  if (n == null || !Number.isFinite(n)) return '—';
  const a = Math.abs(n);
  if (a >= 1e9) return `${n < 0 ? '-' : ''}$${(a / 1e9).toFixed(1)}B`;
  if (a >= 1e6) return `${n < 0 ? '-' : ''}$${(a / 1e6).toFixed(1)}M`;
  if (a >= 1e3) return `${n < 0 ? '-' : ''}$${(a / 1e3).toFixed(0)}K`;
  return `${n < 0 ? '-' : ''}$${a.toFixed(0)}`;
};

// ---- timestamp -------------------------------------------------------------
const now = new Date();
const p2 = (n) => String(n).padStart(2, '0');
const stamp = `${now.getFullYear()}-${p2(now.getMonth() + 1)}-${p2(now.getDate())}_${p2(now.getHours())}${p2(now.getMinutes())}`;

// ---------------------------------------------------------------------------
async function gather(ticker, AGENT_KEY) {
  const T = ticker.toUpperCase();
  const auth = AGENT_KEY ? { Authorization: `Bearer ${AGENT_KEY}` } : {};
  const health = {};
  const raw = {};

  // --- 1. ticker snapshot (technicals + options positioning) ---------------
  const tk = await getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(T)}`, auth);
  raw.ticker = tk.data ?? { error: tk.error, status: tk.status };
  health.ticker = tk.ok ? 'ok' : `FAILED (${tk.status === 401 || tk.status === 403 ? (AGENT_KEY ? 'key rejected' : 'no AGENT_API_KEY') : tk.error})`;

  // --- 2. options flow (per-ticker unusual activity) -----------------------
  const flow = [];
  let flowFail = false;
  for (let pg = 1; pg <= FLOW_PAGES; pg++) {
    const r = await getJson(`${TD_BASE}/api/agent/unusual-activity?ticker=${encodeURIComponent(T)}&timeFrame=${FLOW_TIMEFRAME}&page=${pg}&pageSize=${FLOW_PAGE_SIZE}`, auth);
    if (!r.ok) { flowFail = true; break; }
    const rows = (r.data && r.data.data) || [];
    flow.push(...rows);
    if (rows.length < FLOW_PAGE_SIZE) break;
  }
  raw.flow = flow;
  health.flow = flowFail ? `FAILED (${AGENT_KEY ? 'key rejected' : 'no AGENT_API_KEY'})` : `${flow.length} alerts (${FLOW_TIMEFRAME})`;

  // --- 3. institutional ownership (TickerTrace 13F) ------------------------
  const tt = await getJson(`${TT_BASE}/ticker/${encodeURIComponent(T)}`);
  raw.tickertrace = tt.data ?? { error: tt.error, status: tt.status };
  health.tickertrace = tt.ok ? `${tt.data?.fundCount ?? 0} funds` : (tt.status === 404 ? 'no 13F coverage' : `FAILED (${tt.error})`);

  return { T, health, raw, tk: tk.data, flow, tt: tt.data };
}

function analyzeFlow(flow) {
  let bull = 0, bear = 0, callPrem = 0, putPrem = 0, maxScore = 0, repeat = 0, inst = false;
  const big = [];
  for (const a of flow) {
    const prem = num(a.premium) || 0;
    const s = (a.sentiment || a.sentimentLabel || '');
    if (/bull/i.test(s)) bull += prem; else if (/bear/i.test(s)) bear += prem;
    if (/call/i.test(a.type || '')) callPrem += prem; else if (/put/i.test(a.type || '')) putPrem += prem;
    maxScore = Math.max(maxScore, num(a.score) || 0);
    if ((num(a.repeatCount) || 0) > 1 || a.isRepeatFlow) repeat = Math.max(repeat, num(a.repeatCount) || 2);
    if (/institutional/i.test(a.tierDescription || '')) inst = true;
    big.push(a);
  }
  big.sort((x, y) => (num(y.premium) || 0) - (num(x.premium) || 0));
  return { count: flow.length, bull, bear, net: bull - bear, callPrem, putPrem, maxScore, repeat, inst, big: big.slice(0, 8) };
}

function buildDossier(T, data, chartPath) {
  const { health, tk, flow, tt } = data;
  const t = (tk && tk.technicals) || {};
  const o = (tk && tk.options) || {};
  const L = [];

  L.push(`# 🔬 Deep Dive — ${T}${t.name ? ` · ${t.name}` : ''}`);
  L.push('');
  L.push(`_Generated ${now.toString()}_`);
  L.push('');

  // --- snapshot ---
  const price = num(tk?.price) ?? num(t.close);
  const chg = num(t.change);
  const chgPct = (chg != null && price != null && (price - chg) !== 0) ? (chg / (price - chg) * 100) : null;
  L.push(`**Price** $${f2(price)}${chgPct != null ? ` (${pct(chgPct)} today)` : ''}${t.sector ? ` · ${t.sector}` : ''}`);
  if (t.high90d != null && t.low90d != null && price != null) {
    const range = (price - t.low90d) / (t.high90d - t.low90d) * 100;
    L.push(`**90-day range** $${f2(t.low90d)} → $${f2(t.high90d)} · currently **${f0(range)}% up the range**`);
  }
  L.push('');

  // --- data health ---
  L.push('| Leg | Status |');
  L.push('|---|---|');
  L.push(`| Ticker / technicals / options (TD Pro) | ${health.ticker} |`);
  L.push(`| Options flow (TD Pro) | ${health.flow} |`);
  L.push(`| 13F ownership (TickerTrace) | ${health.tickertrace} |`);
  L.push(`| Chart | ${chartPath ? 'rendered' : 'not rendered'} |`);
  L.push('');

  // --- technicals ---
  L.push('## 📐 Technicals');
  L.push('');
  if (Object.keys(t).length) {
    const stackUp = /bull/i.test(t.emaStack || '');
    L.push('| Metric | Value | | Metric | Value |');
    L.push('|---|---|---|---|---|');
    L.push(`| RSI(14) | ${f0(t.rsi)} | | EMA stack | ${t.emaStack || '—'} |`);
    L.push(`| ADX | ${f0(t.adx)} | | Trend | ${t.trendStatus || '—'} |`);
    L.push(`| Stoch %K | ${f0(t.stochK)} | | Buy zone | ${t.buyZone || '—'} |`);
    L.push(`| MACD | ${f2(t.macd)} | | Squeeze ratio | ${f2(t.squeezeRatio)} |`);
    L.push(`| ATR | ${f2(t.atr)} | | ATR× from EMA21 | ${f2(t.atrMultipleFromEma21)} |`);
    L.push(`| Williams %R | ${f0(t.williamsR)} | | CCI | ${f0(t.cci)} |`);
    L.push(`| Rel volume | ${f2(t.relVol)} | | Bollinger %B | ${f0(t.bbPct)} |`);
    L.push('');
    L.push('**EMA / SMA ladder** (where price sits in the moving-average stack):');
    L.push('');
    L.push('| EMA8 | EMA21 | EMA55 | EMA89 | SMA50 | SMA200 |');
    L.push('|---|---|---|---|---|---|');
    L.push(`| ${f2(t.ema8)} | ${f2(t.ema21)} | ${f2(t.ema55)} | ${f2(t.ema89)} | ${f2(t.sma50)} | ${f2(t.sma200)} |`);
    L.push('');
    if (price != null) {
      const vs = (lvl) => (lvl ? `${price >= lvl ? 'above' : 'below'} ${f2(lvl)}` : '—');
      L.push(`Price is **${vs(t.ema21)}** EMA21, **${vs(t.sma200)}** SMA200. EMA stack is **${stackUp ? 'bullish (fast > slow)' : (t.emaStack || 'mixed')}**.`);
      L.push('');
    }
    L.push('**Key levels** — pivots & fib retrace:');
    L.push('');
    L.push('| S2 | S1 | Pivot | R1 | R2 | | Fib .382 | Fib .500 | Fib .618 |');
    L.push('|---|---|---|---|---|---|---|---|---|');
    L.push(`| ${f2(t.pivotS2)} | ${f2(t.pivotS1)} | ${f2(t.pivot)} | ${f2(t.pivotR1)} | ${f2(t.pivotR2)} | | ${f2(t.fib382)} | ${f2(t.fib500)} | ${f2(t.fib618)} |`);
    L.push('');
    if (t.keltnerLower != null) {
      L.push(`Keltner channel: ${f2(t.keltnerLower)} / ${f2(t.keltnerMiddle)} / ${f2(t.keltnerUpper)} — price is **${t.keltnerState || '—'}**.`);
      L.push('');
    }
    if (t.bounceState && t.bounceState !== 'neutral') {
      L.push(`Bounce state: **${t.bounceState}** (composite ${t.bounceComposite}, ${t.bounceBotCount} bottom / ${t.bounceTopCount} top signals).`);
      L.push('');
    }
  } else {
    L.push('_Technicals unavailable (ticker leg failed)._');
    L.push('');
  }

  // --- options positioning ---
  L.push('## 🎯 Options positioning');
  L.push('');
  if (Object.keys(o).length) {
    const em = o.expectedMove || {};
    const skew = o.ivSkew || {};
    L.push(`- **Max pain:** $${f2(o.maxPain)} · **Call wall:** $${f2(o.callWall)} (resistance) · **Put wall:** $${f2(o.putWall)} (support)`);
    if (em.percent != null) L.push(`- **Expected move (to ${tk?.expiration || 'next exp'}, ${tk?.dte ?? '?'} DTE):** ±${f2(em.percent)}% → $${f2(em.lower)} – $${f2(em.upper)}`);
    if (skew.skew != null) L.push(`- **IV skew:** ${f2(skew.skew)} (put IV ${f2(skew.putIV)} vs call IV ${f2(skew.callIV)}) — dealer read **${skew.sentiment || '—'}**`);
    if (o.putCallOIRatio != null) L.push(`- **Put/Call OI ratio:** ${f2(o.putCallOIRatio)} ${o.putCallOIRatio < 0.8 ? '(call-heavy)' : o.putCallOIRatio > 1.2 ? '(put-heavy)' : '(balanced)'}`);
    L.push('');
    const ts = (o.topStrikes || []).slice(0, 6);
    if (ts.length) {
      L.push('**Biggest open-interest strikes:**');
      L.push('');
      L.push('| Strike | Total OI | Call OI | Put OI | Dominant | % of total |');
      L.push('|---|---|---|---|---|---|');
      for (const s of ts) L.push(`| $${f2(s.strike)} | ${f0(s.totalOI)} | ${f0(s.callOI)} | ${f0(s.putOI)} | ${s.dominant || '—'} | ${f0(s.pctOfTotal)}% |`);
      L.push('');
    }
  } else {
    L.push('_Options positioning unavailable._');
    L.push('');
  }

  // --- options flow ---
  L.push('## 💰 Options flow (unusual activity)');
  L.push('');
  if (flow && flow.length) {
    const fa = analyzeFlow(flow);
    L.push(`Over the last **${FLOW_TIMEFRAME}**: ${fa.count} alerts. Bullish premium **${fmt$(fa.bull)}** vs bearish **${fmt$(fa.bear)}** → net **${fmt$(fa.net)} ${fa.net > 0 ? 'Bullish' : fa.net < 0 ? 'Bearish' : 'Mixed'}**. Call premium ${fmt$(fa.callPrem)} vs put ${fmt$(fa.putPrem)}.${fa.inst ? ' 🛡️ Institutional-alpha tier present.' : ''}${fa.repeat > 1 ? ` 🔁 repeat-strike conviction ×${fa.repeat}.` : ''}`);
    L.push('');
    L.push('**Largest premium trades:**');
    L.push('');
    L.push('| When | Type | Strike | Exp | Premium | Sentiment | Score | Note |');
    L.push('|---|---|---|---|---|---|---|---|');
    for (const a of fa.big) {
      L.push(`| ${a.time || '—'} | ${a.type || '—'} | $${f2(num(a.strike))} | ${a.expiry || '—'} | ${fmt$(num(a.premium))} | ${a.sentiment || '—'} | ${f0(num(a.score))} | ${(a.tradeType || '').slice(0, 14)}${a.isRepeatFlow ? ' 🔁' : ''} |`);
    }
    L.push('');
  } else {
    L.push(`_No qualifying flow for ${T} over the last ${FLOW_TIMEFRAME} (quiet, or flow leg unavailable)._`);
    L.push('');
  }

  // --- institutional ownership ---
  L.push('## 🏛️ Institutional ownership (13F — TickerTrace)');
  L.push('');
  if (tt && Array.isArray(tt.holdings) && tt.holdings.length) {
    L.push(`Held by **${tt.fundCount ?? tt.holdings.length} funds** in TickerTrace coverage (combined weight across those funds: ${f2(tt.totalWeight)}).`);
    L.push('');
    L.push('**Top holders by portfolio weight:**');
    L.push('');
    L.push('| Fund | Provider | Weight % | Shares | Type |');
    L.push('|---|---|---|---|---|');
    for (const h of tt.holdings.slice(0, 12)) {
      L.push(`| ${h.fund || '—'} | ${h.provider || '—'} | ${f2(num(h.weight))}% | ${f0(num(h.shares))} | ${h.isOption ? 'option' : 'shares'} |`);
    }
    L.push('');
    const changes = (tt.changes || []).filter((c) => num(c.weightDelta) != null);
    if (changes.length) {
      const adds = changes.filter((c) => num(c.weightDelta) > 0).sort((a, b) => num(b.weightDelta) - num(a.weightDelta));
      const trims = changes.filter((c) => num(c.weightDelta) < 0).sort((a, b) => num(a.weightDelta) - num(b.weightDelta));
      L.push(`**Recent 13F changes:** ${adds.length} adds, ${trims.length} trims.`);
      L.push('');
      L.push('| Fund | Action | Δ weight | Current wt | Type | Detail |');
      L.push('|---|---|---|---|---|---|');
      for (const c of [...adds.slice(0, 6), ...trims.slice(0, 6)]) {
        const od = c.optionDetails ? `${od_str(c)}` : '';
        L.push(`| ${c.fund || '—'} | ${c.type || (num(c.weightDelta) > 0 ? 'ADDED' : 'TRIMMED')} | ${pct(num(c.weightDelta))} | ${f2(num(c.currentWeight))}% | ${c.isOption ? 'option' : 'shares'} | ${od} |`);
      }
      L.push('');
    }
    L.push('> Note: this is fund/ETF holdings coverage (incl. thematic + option-overlay ETFs), not pure long-only conviction. Read provider + type — a YieldMax/Roundhill option overlay is income mechanics, not a directional bet.');
    L.push('');
  } else {
    L.push(`_No 13F coverage for ${T} in TickerTrace${health.tickertrace.includes('FAILED') ? ' (leg failed)' : ''}._`);
    L.push('');
  }

  // --- chart ---
  if (chartPath) {
    L.push('## 📉 Chart');
    L.push('');
    L.push(`90-day candles + EMA 8/21/55 + SMA200 + volume + RSI: \`${chartPath}\``);
    L.push('');
  }

  L.push('---');
  L.push('_TD Pro technicals/options/flow + TickerTrace 13F. No news in this pull — check recent catalysts separately. Raw JSON saved under `raw/`._');
  return L.join('\n');
}

function od_str(c) {
  const d = c.optionDetails || {};
  return `${d.type || ''} $${d.strike ?? '?'} ${d.expiry || ''}`.trim();
}

// ---------------------------------------------------------------------------
async function main() {
  const tickers = process.argv.slice(2).map((s) => s.toUpperCase().replace(/[^A-Z.]/g, '')).filter(Boolean);
  if (!tickers.length) {
    console.error('Usage: node dossier.mjs TICKER [TICKER ...]');
    process.exit(2);
  }
  const AGENT_KEY = await loadAgentKey();
  const OUT_DIR = join(SKILL_DIR, 'runs', `${tickers.join('-')}_${stamp}`);
  const RAW_DIR = join(OUT_DIR, 'raw');
  const CHART_DIR = join(OUT_DIR, 'charts');
  await mkdir(RAW_DIR, { recursive: true });

  // render all charts in one python call (reuse stock-recap venv + renderer)
  const charts = {};
  try {
    const { execFileSync } = await import('node:child_process');
    const py = join(RECAP_DIR, '.venv', 'bin', 'python');
    const script = join(RECAP_DIR, 'scripts', 'render_chart.py');
    if (existsSync(py) && existsSync(script)) {
      const out = execFileSync(py, [script, ...tickers, '--out', CHART_DIR],
        { encoding: 'utf8', timeout: 180000, env: { ...process.env, AGENT_API_KEY: AGENT_KEY || '' } });
      for (const line of out.split('\n')) {
        const [t, p] = line.split('\t');
        if (t && p && !/^ERROR/.test(p.trim())) charts[t.trim()] = p.trim();
      }
    }
  } catch { /* chart is best-effort; the dossier still completes without it */ }

  const results = [];
  for (const T of tickers) {
    const data = await gather(T, AGENT_KEY);
    for (const [k, v] of Object.entries(data.raw)) {
      await writeFile(join(RAW_DIR, `${T}_${k}.json`), JSON.stringify(v, null, 2));
    }
    const md = buildDossier(T, data, charts[T] || null);
    const docPath = join(OUT_DIR, `${T}_dossier.md`);
    await writeFile(docPath, md);
    console.log(md);
    console.log('\n──────────────────────────────────────────\n');
    results.push({ ticker: T, dossier: docPath, chart: charts[T] || null, health: data.health });
  }

  console.log(`📄 Saved under: ${OUT_DIR}`);
  console.log(JSON.stringify({ outDir: OUT_DIR, results }, null, 0));
}

main().catch((e) => { console.error('dossier.mjs fatal:', e); process.exit(1); });
