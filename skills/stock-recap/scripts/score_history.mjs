#!/usr/bin/env node
// stock-recap / score_history.mjs
// Grades past runs against what actually happened. For every run old enough to
// have a forward window, it looks up each shortlist name's price N trading days
// later and computes the forward return — then rolls a hit-rate scorecard the
// recap itself reads back in ("Track record: hit-rate X%, median Y%").
//
// This is the honesty check on the list: convergence ranking is only worth
// anything if the names it surfaces actually go up. Buckets the results so we
// can see whether the Reversal-Watch edge and higher-leg convergence really do
// outperform the base shortlist.
//
// Forward prices come from the SAME source the run used — the OLD agent API
// /api/agent/ticker/:symbol/chart-data (no new dependency). Best-effort and
// idempotent: a run with a scored.json is skipped unless --rescore is passed.
//
// Usage:  node .claude/skills/stock-recap/scripts/score_history.mjs [--rescore] [--horizon 5]

import { writeFile, readFile, readdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');
const RUNS_DIR = join(SKILL_DIR, 'runs');

const TD_BASE = process.env.TD_API_URL || 'https://traderdaddy-pro-whop-production.up.railway.app';
const TIMEOUT_MS = Number(process.env.RECAP_TIMEOUT_MS || 60000);

const argv = process.argv.slice(2);
const RESCORE = argv.includes('--rescore');
const HORIZON = Number((argv[argv.indexOf('--horizon') + 1] && argv.includes('--horizon')) ? argv[argv.indexOf('--horizon') + 1] : (process.env.RECAP_HORIZON || 5));

const BASE_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
  Accept: 'application/json',
};

// ---- helpers --------------------------------------------------------------
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
async function getJson(url, headers = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { headers: { ...BASE_HEADERS, ...headers }, signal: ctrl.signal });
    const text = await res.text();
    let data; try { data = JSON.parse(text); } catch { data = null; }
    if (!res.ok) return { ok: false, status: res.status, error: (data && data.error) || text.slice(0, 120) };
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? 'timeout' : e.message };
  } finally { clearTimeout(t); }
}
// stamp "2026-06-09_0701" -> Date at that local time
function stampToDate(stamp) {
  const m = stamp.match(/^(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})$/);
  if (!m) return null;
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4]), Number(m[5]));
}
function tradingDaysBetween(a, b) { // rough calendar→trading scale
  return Math.floor((b - a) / 86400000 * (5 / 7));
}
const median = (xs) => {
  const a = xs.filter((x) => Number.isFinite(x)).sort((x, y) => x - y);
  if (!a.length) return null;
  const mid = Math.floor(a.length / 2);
  return a.length % 2 ? a[mid] : (a[mid - 1] + a[mid]) / 2;
};
function bucketStats(picks) {
  const fwds = picks.map((p) => p.fwdPct).filter((x) => Number.isFinite(x));
  if (!fwds.length) return { n: 0, hitRate: null, medianFwdPct: null, avgFwdPct: null };
  const wins = fwds.filter((x) => x > 0).length;
  // Excess vs SPY over the identical window. Without this the card reports beta as
  // skill: on 2026-08-04 the raw card read "48% hit, roughly flat" while the same
  // picks were behind a passive SPY hold on 61% of names.
  const exs = picks.map((p) => p.excessPct).filter((x) => Number.isFinite(x));
  return {
    n: fwds.length,
    hitRate: wins / fwds.length,
    medianFwdPct: median(fwds),
    avgFwdPct: fwds.reduce((s, x) => s + x, 0) / fwds.length,
    beatSpyRate: exs.length ? exs.filter((x) => x > 0).length / exs.length : null,
    medianExcessPct: median(exs),
    avgExcessPct: exs.length ? exs.reduce((s, x) => s + x, 0) / exs.length : null,
  };
}

// the candidate's date-stamped close N trading days after the run.
// chartData rows are trading days only, so "N rows after entry" == N trading days.
function fwdReturnFromChart(chartData, runDate, entryFallback) {
  if (!Array.isArray(chartData) || chartData.length < HORIZON + 1) return null;
  const rows = chartData
    .map((r) => ({ date: new Date(r.date), close: Number(r.close) }))
    .filter((r) => Number.isFinite(r.close) && !isNaN(r.date))
    .sort((a, b) => a.date - b.date);
  // entry = last close on/before the run date; exit = HORIZON rows later
  let entryIdx = -1;
  for (let i = 0; i < rows.length; i++) {
    if (rows[i].date <= runDate) entryIdx = i; else break;
  }
  if (entryIdx < 0) return null;
  const exitIdx = entryIdx + HORIZON;
  if (exitIdx >= rows.length) return null; // not enough forward data yet
  const entry = rows[entryIdx].close || entryFallback;
  const exit = rows[exitIdx].close;
  if (!Number.isFinite(entry) || !entry || !Number.isFinite(exit)) return null;
  return {
    entry, exit, entryDate: rows[entryIdx].date.toISOString().slice(0, 10),
    exitDate: rows[exitIdx].date.toISOString().slice(0, 10),
    fwdPct: (exit - entry) / entry * 100,
  };
}

function legKey(legCount) { return legCount >= 4 ? '4plus' : String(legCount); }

// ---------------------------------------------------------------------------
async function main() {
  const KEY = await loadAgentKey();
  const auth = KEY ? { Authorization: `Bearer ${KEY}` } : {};
  const now = new Date();

  if (!existsSync(RUNS_DIR)) { console.error('no runs/ dir yet'); process.exit(0); }
  const entries = await readdir(RUNS_DIR, { withFileTypes: true });
  const runDirs = entries.filter((e) => e.isDirectory() && /^\d{4}-\d{2}-\d{2}_\d{4}$/.test(e.name)).map((e) => e.name).sort();

  const chartCache = new Map(); // ticker -> chartData[]
  const fetchChart = async (ticker) => {
    if (chartCache.has(ticker)) return chartCache.get(ticker);
    const r = await getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(ticker)}/chart-data?days=300`, auth);
    const data = r.ok && r.data ? (r.data.chartData || []) : null;
    chartCache.set(ticker, data);
    return data;
  };

  // SPY benchmark: forward return over the exact same entry/exit dates as each pick.
  const spyChart = await getJson(`${TD_BASE}/api/agent/ticker/SPY/chart-data?days=300`, auth);
  const spyRows = (spyChart.ok && spyChart.data ? (spyChart.data.chartData || []) : [])
    .map((r) => ({ d: String(r.date).slice(0, 10), c: Number(r.close) }))
    .filter((r) => Number.isFinite(r.c))
    .sort((a, b) => (a.d < b.d ? -1 : 1));
  const spyIdx = new Map(spyRows.map((r, i) => [r.d, i]));
  const spyFwdPct = (entryDate) => {
    const i = spyIdx.get(entryDate);
    if (i == null || i + HORIZON >= spyRows.length) return null;
    return (spyRows[i + HORIZON].c - spyRows[i].c) / spyRows[i].c * 100;
  };
  if (!spyRows.length) console.warn('warn: SPY benchmark unavailable, excess columns will be null');

  const allScoredPicks = [];  // across every scored run, for the rolling card
  let runsScored = 0, runsSkippedYoung = 0, runsAlready = 0;

  for (const name of runDirs) {
    const runDir = join(RUNS_DIR, name);
    const slPath = join(runDir, 'raw', 'shortlist.json');
    const scoredPath = join(runDir, 'scored.json');
    if (!existsSync(slPath)) continue;

    const runDate = stampToDate(name);
    if (!runDate) continue;
    if (tradingDaysBetween(runDate, now) < HORIZON) { runsSkippedYoung++; continue; }

    if (existsSync(scoredPath) && !RESCORE) {
      // reuse prior scoring (idempotent, no refetch)
      try {
        const prior = JSON.parse(await readFile(scoredPath, 'utf8'));
        if (Array.isArray(prior.picks)) { allScoredPicks.push(...prior.picks); runsAlready++; continue; }
      } catch { /* fall through to re-score */ }
    }

    let shortlist;
    try { shortlist = JSON.parse(await readFile(slPath, 'utf8')); } catch { continue; }
    if (!Array.isArray(shortlist) || !shortlist.length) continue;

    const picks = [];
    for (const c of shortlist) {
      const ticker = c.ticker;
      if (!ticker) continue;
      const chart = await fetchChart(ticker);
      if (!chart) continue;
      const fr = fwdReturnFromChart(chart, runDate, c.tech?.price);
      if (!fr) continue;
      const spyPct = spyFwdPct(fr.entryDate);
      picks.push({
        run: name, ticker,
        legCount: c.legCount ?? (Array.isArray(c.legs) ? c.legs.length : null),
        reversing: !!(c.reversal && c.reversal.reversing),
        conflict: !!c.conflict,
        entry: fr.entry, exit: fr.exit, entryDate: fr.entryDate, exitDate: fr.exitDate,
        fwdPct: fr.fwdPct,
        spyPct,
        excessPct: Number.isFinite(spyPct) ? fr.fwdPct - spyPct : null,
      });
    }
    if (!picks.length) { runsSkippedYoung++; continue; }

    const scored = {
      run: name, runDate: runDate.toISOString(), horizonDays: HORIZON,
      scoredAt: now.toISOString(), n: picks.length,
      overall: bucketStats(picks),
      reversalWatch: bucketStats(picks.filter((p) => p.reversing)),
      picks,
    };
    await writeFile(scoredPath, JSON.stringify(scored, null, 2));
    allScoredPicks.push(...picks);
    runsScored++;
    const o = scored.overall;
    console.log(`scored ${name}: ${picks.length} picks, hit ${(o.hitRate * 100).toFixed(0)}%, median ${o.medianFwdPct?.toFixed(1)}%`);
  }

  // ---- rolling scorecard the recap reads back in --------------------------
  // Dedupe to one run per calendar day. Re-running the skill several times in a
  // day used to count the same picks 2-10x, which inflated n and made correlated
  // errors look like independent evidence (7/19 alone was 10 runs).
  const lastRunOfDay = {};
  for (const p of allScoredPicks) {
    const day = p.run.slice(0, 10);
    if (!lastRunOfDay[day] || p.run > lastRunOfDay[day]) lastRunOfDay[day] = p.run;
  }
  const dedupedPicks = allScoredPicks.filter((p) => p.run === lastRunOfDay[p.run.slice(0, 10)]);

  const byLeg = {};
  for (const k of ['2', '3', '4plus']) byLeg[k] = bucketStats(dedupedPicks.filter((p) => legKey(p.legCount) === k));
  const card = {
    generatedAt: now.toISOString(),
    horizonDays: HORIZON,
    runsScored: runsScored + runsAlready,
    tradingDays: Object.keys(lastRunOfDay).length,
    totalPicks: dedupedPicks.length,
    rawPicksBeforeDedupe: allScoredPicks.length,
    benchmark: 'SPY, same entry/exit dates',
    overall: bucketStats(dedupedPicks),
    buckets: {
      reversalWatch: bucketStats(dedupedPicks.filter((p) => p.reversing)),
      conflict: bucketStats(dedupedPicks.filter((p) => p.conflict)),
      clean: bucketStats(dedupedPicks.filter((p) => !p.conflict)),
      byLegCount: byLeg,
    },
  };
  // normalize hitRate to 0–1 fractions (what the recap's pctRaw expects)
  await writeFile(join(RUNS_DIR, '_scorecard.json'), JSON.stringify(card, null, 2));

  const o = card.overall;
  console.log('\n──────────────────────────────────────────');
  console.log(`📊 Scorecard: ${card.totalPicks} picks across ${card.tradingDays} trading days (${HORIZON}-day forward, vs SPY)`);
  const ex = (b) => b.medianExcessPct == null ? '' : `  |  vs SPY ${b.medianExcessPct >= 0 ? '+' : ''}${b.medianExcessPct.toFixed(1)}% med, beat ${(b.beatSpyRate * 100).toFixed(0)}%`;
  if (o.n) console.log(`   Overall  hit ${(o.hitRate * 100).toFixed(0)}% · median ${o.medianFwdPct?.toFixed(1)}%${ex(o)}`);
  const rw = card.buckets.reversalWatch;
  if (rw.n) console.log(`   Reversal Watch  hit ${(rw.hitRate * 100).toFixed(0)}% · median ${rw.medianFwdPct?.toFixed(1)}% (n=${rw.n})${ex(rw)}`);
  for (const k of ['2', '3', '4plus']) { const b = byLeg[k]; if (b.n) console.log(`   ${(k === '4plus' ? '4+' : k).padEnd(2)}-leg  hit ${(b.hitRate * 100).toFixed(0)}% · median ${b.medianFwdPct?.toFixed(1)}% (n=${b.n})${ex(b)}`); }
  console.log(`\n   ${runsScored} newly scored, ${runsAlready} cached, ${runsSkippedYoung} too young.`);
  console.log(`   Written: ${join(RUNS_DIR, '_scorecard.json')}`);
}

main().catch((e) => { console.error('score_history.mjs fatal:', e); process.exit(1); });
