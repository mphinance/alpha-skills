#!/usr/bin/env node
// value-complex / gather.mjs
// Reads Avantis value ETFs (AVUV small-cap, AVLV large-cap) from TickerTrace's
// per-fund holdings endpoint and builds a by-weight, lifecycle-grouped report:
// new/exited, conviction tilt (inflow-stripped), up-streaks, + cross-tier theme.
//
// No auth needed — /fund/<TICKER> is public. Presents a browser User-Agent
// (the edge WAF 403s a bare Node UA). Node 18+ (global fetch).

import { writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');

const TT_BASE = process.env.TICKERTRACE_API_URL || 'https://api.tickertrace.pro/api/v1';
const TIMEOUT_MS = Number(process.env.VC_TIMEOUT_MS || 30000);
const FUNDS = (process.env.VC_FUNDS || 'AVUV,AVLV').split(',').map((s) => s.trim()).filter(Boolean);
const TIER = { AVUV: 'small-cap value', AVMV: 'mid-cap value', AVLV: 'large-cap value' };
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36';
const TOP = Number(process.env.VC_TOP || 8); // rows per bucket
const WEIGHT_FLOOR = Number(process.env.VC_WEIGHT_FLOOR || 0.05); // ignore micro positions in tilt (tiny base = noisy %)
const INFLOW_MAX_TRIMS = 2; // <= this many real share-reductions ⇒ treat the day as an inflow/creation day

// ---- helpers --------------------------------------------------------------
async function getJson(url) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const r = await fetch(url, { signal: ctrl.signal, headers: { 'User-Agent': UA, Accept: 'application/json' } });
    if (!r.ok) return { ok: false, error: `HTTP ${r.status}` };
    return { ok: true, data: await r.json() };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  } finally {
    clearTimeout(t);
  }
}

const median = (xs) => {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};
const pad = (s, n) => String(s ?? '').slice(0, n).padEnd(n);
const sectorShort = (s) => (s || '—').replace('CONSUMER DISCRETIONARY', 'Cons. Disc.')
  .replace('COMMUNICATION SERVICES', 'Comm. Svcs').replace('INFORMATION TECHNOLOGY', 'Info Tech')
  .replace('CONSUMER STAPLES', 'Cons. Staples').replace('HEALTH CARE', 'Health Care')
  .replace('REAL ESTATE', 'Real Estate').replace(/^(\w)(\w+)/, (m, a, b) => a + b.toLowerCase());

// ---- per-fund analysis ----------------------------------------------------
function analyzeFund(d) {
  const isJunk = (t) => !t || t === 'OTHER';
  const changes = (d.recentChanges || []).filter((x) => !x.isOption && !isJunk(x.ticker));
  const stockChanges = changes.filter((x) => x.type === 'CHANGED' && x.previousShares > 0);

  // inflow tide = median share-growth across the book; excess isolates active tilt.
  // impact = excess × weight, so a real over-weight at meaningful size outranks a
  // micro position that doubled off a near-zero base.
  const growth = stockChanges.map((x) => x.sharesDelta / x.previousShares);
  const tide = median(growth);
  const tilted = stockChanges
    .filter((x) => x.sharesDelta !== 0 && x.currentWeight >= WEIGHT_FLOOR)
    .map((x) => {
      const sharePct = x.sharesDelta / x.previousShares;
      const excess = sharePct - tide;
      return { ...x, sharePct, excess, impact: excess * x.currentWeight };
    });

  const newPos = changes.filter((x) => x.type === 'NEW' || (x.previousShares === 0 && x.currentShares > 0));
  const exited = changes.filter((x) => x.type === 'REMOVED' || (x.currentShares === 0 && x.previousShares > 0));
  const adds = changes.filter((x) => x.sharesDelta > 0).length;
  const realTrims = changes.filter((x) => x.sharesDelta < 0).length;
  const inflowDay = realTrims <= INFLOW_MAX_TRIMS && adds > realTrims * 5;
  const streaks = (d.streaks || []).filter((s) => s.direction === 'up' && !isJunk(s.ticker)).sort((a, b) => b.days - a.days);

  // sector map for labeling streaks (streak rows carry no sector)
  const secOf = {};
  for (const x of changes) secOf[x.ticker] = x.sector;

  // sector active-lean = sum of positive excess-impact per sector; + streak counts
  const secLean = {};
  for (const x of tilted) {
    if (x.impact <= 0) continue;
    secLean[x.sector] = (secLean[x.sector] || 0) + x.impact;
  }
  const secStreak = {};
  for (const s of streaks) {
    const sec = secOf[s.ticker] || '?';
    if (sec === '?') continue;
    secStreak[sec] = (secStreak[sec] || 0) + 1;
  }

  return {
    fund: d.fund, tier: TIER[d.fund] || d.category, aum: d.aum, holdings: d.holdingsCount,
    asOf: d.asOfDate || null, tide, adds, realTrims, inflowDay, newPos, exited, tilted, streaks, secOf, secLean, secStreak,
  };
}

// ---- markdown -------------------------------------------------------------
function fundBlock(a) {
  const L = [];
  const flow = a.inflowDay
    ? `**inflows** — ${a.adds} buys vs ${a.realTrims} sells (new money buying the book pro-rata at ≈${(a.tide * 100).toFixed(2)}%/name; tilt below is *above* that tide)`
    : `active rebalancing — ${a.adds} adds vs ${a.realTrims} trims`;
  L.push(`## ${a.tier} — ${a.fund}`);
  L.push(`_$${a.aum}B · ${a.holdings} holdings · flow tell: ${flow}_`);
  L.push('');

  L.push('### 🆕 New / Exited');
  if (!a.newPos.length && !a.exited.length) L.push('_No new or exited names this snapshot._');
  for (const x of a.newPos) L.push(`- 🟢 **NEW ${x.ticker}** — ${x.name.replace(/\s+/g, ' ').trim().slice(0, 36)} · ${sectorShort(x.sector)} · wt ${x.currentWeight.toFixed(3)} · +${Math.round(x.currentShares).toLocaleString()} sh`);
  for (const x of a.exited) L.push(`- 🔴 **EXITED ${x.ticker}** — ${x.name.replace(/\s+/g, ' ').trim().slice(0, 36)} · ${sectorShort(x.sector)} · was wt ${(x.previousWeight || 0).toFixed(3)}`);
  L.push('');

  L.push('### 📈 Conviction tilt — active over-weight (inflow- & price-stripped)');
  L.push(`_Share growth minus the fund's median (tide ${(a.tide * 100).toFixed(2)}%); ranked by excess × weight. Positions ≥${WEIGHT_FLOOR}% weight only._`);
  L.push('| Lean | Ticker | Sector | Wt% | Share Δ% | Excess vs tide |');
  L.push('|---|---|---|---|---|---|');
  const up = [...a.tilted].filter((x) => x.impact > 0).sort((x, y) => y.impact - x.impact).slice(0, TOP);
  for (const x of up) L.push(`| ➕ into | **${x.ticker}** | ${sectorShort(x.sector)} | ${x.currentWeight.toFixed(2)} | +${(x.sharePct * 100).toFixed(2)}% | +${(x.excess * 100).toFixed(2)}pp |`);
  const dnLabel = a.inflowDay ? 'Bought *below* the tide (relative underweight — least-favored)' : 'Active trims';
  const dn = [...a.tilted].filter((x) => x.impact < 0).sort((x, y) => x.impact - y.impact).slice(0, 4);
  if (dn.length) {
    L.push(`\n_${dnLabel}:_ ` + dn.map((x) => `${x.ticker} (${sectorShort(x.sector)}, ${(x.sharePct * 100).toFixed(2)}%)`).join(' · '));
  }
  L.push('');

  L.push('### 🔥 Up-streaks — momentum leaders');
  if (!a.streaks.length) L.push('_None active._');
  else {
    L.push(a.streaks.slice(0, 12).map((s) => `${s.ticker} ${s.days}d (${sectorShort(a.secOf[s.ticker] || '?')})`).join(' · '));
    const bySec = Object.entries(a.secStreak).sort((x, y) => y[1] - x[1]);
    L.push('');
    L.push('_By sector:_ ' + bySec.map(([s, n]) => `${sectorShort(s)} ${n}`).join(' · '));
  }
  L.push('');
  return L.join('\n');
}

function crossTier(analyses) {
  const tiers = analyses.map((a) => a.fund).join(' / ');
  const L = ['## 🔗 Cross-tier synthesis — what small + large value agree on', ''];
  // convergence = up-streaks in the same sector in EVERY fund (≥2 each), ranked by total.
  const sectors = new Set();
  for (const a of analyses) Object.keys(a.secStreak).forEach((s) => sectors.add(s));
  const rows = [];
  for (const sec of sectors) {
    const strk = analyses.map((a) => (a.secStreak[sec] || 0));
    if (!strk.every((n) => n >= 2)) continue;
    const leanBoth = analyses.every((a) => (a.secLean[sec] || 0) > 0);
    rows.push({ sec, strk, total: strk.reduce((x, y) => x + y, 0), leanBoth });
  }
  rows.sort((x, y) => y.total - x.total);
  if (!rows.length) L.push('_No sector is streaking up (≥2 names) in both funds this snapshot._');
  else {
    L.push(`Sectors with momentum (≥2 up-streaks) in **both** tiers — the value-wide theme:`);
    L.push('');
    L.push(`| Sector | Up-streaks (${tiers}) | Also active over-weight in both? |`);
    L.push('|---|---|---|');
    for (const r of rows) L.push(`| **${sectorShort(r.sec)}** | ${r.strk.join(' / ')} | ${r.leanBoth ? '✅' : '—'} |`);
  }
  L.push('');
  // exact-ticker overlap (rare across tiers, but flag the genuine ones)
  const streakSets = analyses.map((a) => new Set(a.streaks.map((s) => s.ticker)));
  const overlap = [...streakSets[0]].filter((t) => streakSets.every((s) => s.has(t)));
  if (overlap.length) L.push('_Same ticker streaking in both tiers:_ ' + overlap.join(', '));
  return L.join('\n');
}

// ---- main -----------------------------------------------------------------
async function main() {
  const now = new Date();
  const stamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
  const runDir = join(SKILL_DIR, 'runs', stamp);
  const rawDir = join(runDir, 'raw');
  await mkdir(rawDir, { recursive: true });

  // the per-fund endpoint is undated; borrow the freshness stamp from the dated aggregate feed
  let asOf = null;
  const stampR = await getJson(`${TT_BASE}/institutional?limit=1`);
  if (stampR.ok) asOf = stampR.data?.asOfDate || null;

  const analyses = [];
  for (const f of FUNDS) {
    const r = await getJson(`${TT_BASE}/fund/${f}`);
    if (!r.ok) { console.error(`! ${f}: ${r.error}`); continue; }
    await writeFile(join(rawDir, `fund_${f}.json`), JSON.stringify(r.data, null, 2));
    analyses.push(analyzeFund(r.data));
  }
  if (!analyses.length) { console.error('No funds fetched — aborting.'); process.exit(1); }

  const L = [];
  L.push(`# 🏛️ Avantis Value Complex — ${stamp.replace('_', ' ')}`);
  L.push('');
  L.push(`_Per-fund holdings from TickerTrace${asOf ? ` · data as-of **${asOf}**` : ''}. Small + large value, by weight._`);
  L.push('');
  L.push('| Fund | Tier | AUM | Holdings | Adds / Trims |');
  L.push('|---|---|---|---|---|');
  for (const a of analyses) L.push(`| **${a.fund}** | ${a.tier} | $${a.aum}B | ${a.holdings} | ${a.adds} / ${a.realTrims} |`);
  L.push('');
  for (const a of analyses) L.push(fundBlock(a));
  if (analyses.length > 1) L.push(crossTier(analyses));
  L.push('');
  L.push('---');
  L.push('_Inflow-stripped tilt = each name\'s share growth minus the fund\'s median share growth (the inflow tide). Positive excess = genuine active over-weight, not just riding inflows. Raw weightDelta is intentionally not the headline — it blends price drift with share change._');

  const report = L.join('\n');
  const reportPath = join(runDir, 'report.md');
  await writeFile(reportPath, report);
  console.log(report);
  console.log('\n──────────────────────────────────────────');
  console.log(`📄 Report:   ${reportPath}`);
  console.log(JSON.stringify({ reportPath, rawDir, funds: analyses.map((a) => a.fund), asOf }));
}

main().catch((e) => { console.error(e); process.exit(1); });
