#!/usr/bin/env node
// stock-recap / run_and_commit.mjs
// Cron entrypoint: run the daily recap, snapshot its output into the tracked
// `history/` dir (the run dirs under runs/ are gitignored), and git-commit it so
// the recap + watch-list evolution is kept in version history.
//
//   node .claude/skills/stock-recap/scripts/run_and_commit.mjs
//
// Writes (all git-tracked, one per calendar day; reruns overwrite the day):
//   history/<YYYY-MM-DD>.md    — the full markdown report
//   history/<YYYY-MM-DD>.json  — a compact JSON summary (shortlist + health + watchlist)
//   history/_watchlist.json    — snapshot of the persistent cross-run watch store
// Then commits ONLY those paths (never the rest of the working tree) and pushes.

import { execFileSync } from 'node:child_process';
import { writeFile, mkdir, copyFile, readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');
const RUNS_DIR = join(SKILL_DIR, 'runs');
const HIST_DIR = join(SKILL_DIR, 'history');
const GATHER = join(__dirname, 'gather.mjs');
const WATCH_STORE = join(RUNS_DIR, '_watchlist.json');

const git = (args) => execFileSync('git', args, { cwd: SKILL_DIR, encoding: 'utf8' });

async function main() {
  await mkdir(HIST_DIR, { recursive: true });

  // 1. run the recap; the final stdout line is a JSON result object
  const out = execFileSync('node', [GATHER], { encoding: 'utf8', maxBuffer: 128 * 1024 * 1024 });
  const lastLine = out.trim().split('\n').filter(Boolean).pop() || '';
  let result;
  try { result = JSON.parse(lastLine); }
  catch { console.error('run_and_commit: could not parse gather.mjs result line'); process.exit(1); }

  // 2. derive the run stamp / calendar date from the report path
  const reportPath = result.reportPath;
  if (!reportPath || !existsSync(reportPath)) { console.error('run_and_commit: report.md missing'); process.exit(1); }
  const stamp = dirname(reportPath).split('/').pop();        // e.g. 2026-07-19_1248
  const date = (stamp.split('_')[0]) || new Date().toISOString().slice(0, 10);

  // 3. snapshot report.md + a compact JSON summary + the watch-store into history/
  const mdOut = join(HIST_DIR, `${date}.md`);
  const jsonOut = join(HIST_DIR, `${date}.json`);
  const wlOut = join(HIST_DIR, '_watchlist.json');
  await copyFile(reportPath, mdOut);

  let watchlist = null;
  if (existsSync(WATCH_STORE)) {
    try { watchlist = JSON.parse(await readFile(WATCH_STORE, 'utf8')); } catch { /* skip */ }
    await copyFile(WATCH_STORE, wlOut);
  }
  const summary = {
    date, stamp, generatedAt: new Date().toISOString(),
    shortlist: result.shortlist || [],
    health: result.health || {},
    watchlist: watchlist ? { count: Object.keys(watchlist.names || {}).length, names: watchlist.names } : null,
  };
  await writeFile(jsonOut, JSON.stringify(summary, null, 2));

  // 4. commit ONLY the history paths (restrict with pathspec so the rest of the
  //    working tree is never swept in). Untracked files need an explicit add first.
  const paths = [mdOut, jsonOut];
  if (existsSync(wlOut)) paths.push(wlOut);
  git(['add', '--', ...paths]);
  const staged = git(['diff', '--cached', '--name-only', '--', ...paths]).trim();
  if (!staged) { console.log(`run_and_commit: no history changes for ${date} — nothing to commit`); return; }

  const n = summary.watchlist ? summary.watchlist.count : 0;
  const msg = `stock-recap: ${date} recap (${summary.shortlist.length} shortlist, ${n} on watch)`;
  git(['commit', '-m', msg, '--', ...paths]);
  const hash = git(['rev-parse', '--short', 'HEAD']).trim();
  console.log(`run_and_commit: committed ${hash} — ${msg}`);

  // 5. push (commit is already safe on disk if this fails — don't crash the run)
  try {
    git(['push']);
    console.log(`run_and_commit: pushed ${hash} to ${git(['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}']).trim()}`);
  } catch (e) {
    console.error(`run_and_commit: push failed (commit ${hash} is saved locally): ${e?.message || e}`);
  }
}

main().catch((e) => { console.error('run_and_commit failed:', e?.message || e); process.exit(1); });
