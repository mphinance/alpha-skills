#!/usr/bin/env node
// render_chart.mjs — recap charts that don't look like matplotlib.
//
// Renders TD Pro candles as hand-built SVG in a headless browser, in the Gamma Map
// palette (docs/gex-chart/index.html), with the dealer levels drawn on top the way
// the DaddyHUD extension draws them on TradingView: red resistance / green support /
// amber pin / purple gamma flip, each with a right-edge price tag and its OI.
//
// Usage:
//   node render_chart.mjs WULF GOOGL --out /tmp/charts [--days 300] [--no-gex]
//
// Keys: .env_agent_api (bare Bearer token) for candles, .env_td_api (bare X-API-Key)
// for GEX. Both files hold the raw key on one line, NOT key=value.

import { readFileSync, mkdirSync, existsSync } from 'fs';
import { join, resolve, dirname } from 'path';
import { homedir } from 'os';

// playwright is installed once, under the mph-figure skill — reuse that copy rather
// than vendoring a second ~150MB browser bundle into this skill.
const PW_HOME = join(homedir(), '.claude/skills/mph-figure/node_modules/playwright/index.mjs');
const { chromium } = await import(existsSync(PW_HOME) ? PW_HOME : 'playwright');

const AGENT_BASE = 'https://traderdaddy-pro-whop-production.up.railway.app';
const DEV_BASE = 'https://api.traderdaddy.pro/api/v1';

const C = {
  bg: '#0a0a0e', panel: '#101018', line: '#1c1c28', text: '#e6e6ee', dim: '#8a8aa0',
  up: '#00d68f', down: '#ff4d6d',
  ema8: '#00f3ff', ema21: '#ffb000', ema55: '#a855f7', sma200: '#6b6b80',
  support: '#00ff88', resistance: '#ff4d6d', pin: '#ffb000', flip: '#a855f7',
};

// ── keys ────────────────────────────────────────────────────────────────────
function repoRoot(start) {
  let d = resolve(start);
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(d, '.env_agent_api'))) return d;
    const up = dirname(d);
    if (up === d) break;
    d = up;
  }
  return null;
}
const ROOT = repoRoot(process.cwd()) || repoRoot(new URL('.', import.meta.url).pathname);
const readKey = (f) => {
  try { return readFileSync(join(ROOT, f), 'utf8').trim(); } catch { return null; }
};

// ── data ────────────────────────────────────────────────────────────────────
// Both TD endpoints sit behind a bot filter that 403s ("Forbidden / Invalid request")
// on undici's default `node` User-Agent. curl works, plain fetch does not.
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36';

async function fetchCandles(sym, days) {
  const key = readKey('.env_agent_api');
  const r = await fetch(`${AGENT_BASE}/api/agent/ticker/${sym}/chart-data?days=${days}`, {
    headers: { 'User-Agent': UA, ...(key ? { Authorization: `Bearer ${key}` } : {}) },
  });
  const j = await r.json();
  if (!j.chartData) throw new Error(`${sym}: ${j.message || j.error || 'no chartData'}`);
  return j;
}

async function fetchGex(sym) {
  const key = readKey('.env_td_api');
  if (!key) return null;
  try {
    const r = await fetch(`${DEV_BASE}/gex/${sym}`, { headers: { 'X-API-Key': key, 'User-Agent': UA } });
    const j = await r.json();
    return j.success ? j.data : null;
  } catch { return null; }
}

// ── indicators ──────────────────────────────────────────────────────────────
function ema(vals, n) {
  const k = 2 / (n + 1);
  const out = [];
  let prev;
  vals.forEach((v, i) => {
    prev = i === 0 ? v : v * k + prev * (1 - k);
    out.push(i >= n - 1 ? prev : null);
  });
  return out;
}
function sma(vals, n) {
  const out = [];
  let sum = 0;
  vals.forEach((v, i) => {
    sum += v;
    if (i >= n) sum -= vals[i - n];
    out.push(i >= n - 1 ? sum / n : null);
  });
  return out;
}
function rsi(vals, n = 14) {
  const out = [null];
  let ag = 0, al = 0;
  for (let i = 1; i < vals.length; i++) {
    const d = vals[i] - vals[i - 1];
    const g = Math.max(d, 0), l = Math.max(-d, 0);
    if (i <= n) {
      ag += g / n; al += l / n;
      out.push(i === n ? 100 - 100 / (1 + ag / (al || 1e-9)) : null);
    } else {
      ag = (ag * (n - 1) + g) / n;
      al = (al * (n - 1) + l) / n;
      out.push(100 - 100 / (1 + ag / (al || 1e-9)));
    }
  }
  return out;
}

// ── svg ─────────────────────────────────────────────────────────────────────
const W = 1500, H = 900;
const PAD_L = 8, PAD_R = 112, PAD_T = 96;
const PRICE_H = 500, VOL_H = 96, RSI_H = 108, GAP = 18;
const PLOT_W = W - PAD_L - PAD_R;
const VOL_T = PAD_T + PRICE_H + GAP;
const RSI_T = VOL_T + VOL_H + GAP;

const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
// Thinly-traded names come back with a null gammaFlipLevel / maxGammaStrike.
const fmt = (v) => (v == null ? '–' : v >= 1000 ? v.toFixed(0) : v >= 100 ? v.toFixed(1) : v.toFixed(2));
const oiFmt = (v) => (v >= 1000 ? `${Math.round(v / 1000)}k` : String(Math.round(v)));

function buildSvg(sym, meta, candles, gex) {
  const n = candles.length;
  const closes = candles.map((c) => c.close);
  const e8 = ema(closes, 8), e21 = ema(closes, 21), e55 = ema(closes, 55);
  const s200 = sma(closes, 200);
  const rsiv = rsi(closes);

  // Price scale: candles always, plus dealer levels only if they land near the tape.
  let lo = Math.min(...candles.map((c) => c.low));
  let hi = Math.max(...candles.map((c) => c.high));
  const span = hi - lo;
  const levels = [];
  if (gex) {
    const near = (p) => p != null && p > lo - span * 0.12 && p < hi + span * 0.12;
    for (const kl of gex.keyLevels || []) {
      if (!near(kl.strike)) continue;
      const bs = (gex.byStrike || []).find((b) => b.strike === kl.strike);
      const oi = bs ? (bs.callOi || 0) + (bs.putOi || 0) : 0;
      const isPin = kl.strike === gex.maxGammaStrike;
      levels.push({
        price: kl.strike,
        color: isPin ? C.pin : kl.type === 'support' ? C.support : C.resistance,
        label: isPin ? `PIN  ${oiFmt(oi)} OI  MAX GAMMA` : `${kl.type.toUpperCase()}  ${oiFmt(oi)} OI`,
      });
    }
    if (gex.gammaFlipLevel && near(gex.gammaFlipLevel)) {
      levels.push({
        price: gex.gammaFlipLevel,
        color: C.flip,
        label: 'GAMMA FLIP',
        dash: true,
      });
    }
    for (const l of levels) { lo = Math.min(lo, l.price); hi = Math.max(hi, l.price); }
  }
  const padY = (hi - lo) * 0.06;
  lo -= padY; hi += padY;

  const x = (i) => PAD_L + (i + 0.5) * (PLOT_W / n);
  const y = (p) => PAD_T + PRICE_H - ((p - lo) / (hi - lo)) * PRICE_H;
  const cw = Math.max(1.5, Math.min(11, (PLOT_W / n) * 0.62));

  const out = [];
  const push = (s) => out.push(s);

  // panels
  for (const [t, h] of [[PAD_T, PRICE_H], [VOL_T, VOL_H], [RSI_T, RSI_H]]) {
    push(`<rect x="${PAD_L}" y="${t}" width="${PLOT_W}" height="${h}" fill="${C.panel}" stroke="${C.line}"/>`);
  }

  // horizontal price gridlines on round numbers, not on (hi-lo)/6 fractions
  const rawStep = (hi - lo) / 6;
  const mag = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= rawStep) || 10 * mag;
  // Axis labels share the right gutter with the dealer-level tags, so hold them back
  // and draw them once the tags have claimed their rows.
  const axisLabels = [];
  for (let p = Math.ceil(lo / step) * step; p <= hi; p += step) {
    const yy = y(p);
    push(`<line x1="${PAD_L}" y1="${yy}" x2="${PAD_L + PLOT_W}" y2="${yy}" stroke="${C.line}" stroke-dasharray="2 6"/>`);
    axisLabels.push({ p, y: yy });
  }

  // volume
  const vmax = Math.max(...candles.map((c) => c.volume || 0)) || 1;
  candles.forEach((c, i) => {
    const h = ((c.volume || 0) / vmax) * (VOL_H - 8);
    const up = c.close >= c.open;
    push(`<rect x="${x(i) - cw / 2}" y="${VOL_T + VOL_H - h}" width="${cw}" height="${h}" fill="${up ? C.up : C.down}" opacity="0.42"/>`);
  });
  push(`<text x="${PAD_L + 10}" y="${VOL_T + 18}" fill="${C.dim}" font-size="12">VOLUME</text>`);

  // rsi
  const ry = (v) => RSI_T + RSI_H - (v / 100) * RSI_H;
  for (const lv of [30, 50, 70]) {
    push(`<line x1="${PAD_L}" y1="${ry(lv)}" x2="${PAD_L + PLOT_W}" y2="${ry(lv)}" stroke="${lv === 50 ? C.line : '#242433'}" stroke-dasharray="${lv === 50 ? '2 6' : '4 4'}"/>`);
    push(`<text x="${PAD_L + PLOT_W + 10}" y="${ry(lv) + 4}" fill="${C.dim}" font-size="11">${lv}</text>`);
  }
  const rp = rsiv.map((v, i) => (v == null ? null : `${x(i)},${ry(v)}`)).filter(Boolean).join(' ');
  push(`<polyline points="${rp}" fill="none" stroke="#c07bff" stroke-width="1.8"/>`);
  const lastRsi = [...rsiv].reverse().find((v) => v != null);
  push(`<text x="${PAD_L + 10}" y="${RSI_T + 18}" fill="${C.dim}" font-size="12">RSI 14 <tspan fill="${C.text}">${lastRsi ? lastRsi.toFixed(0) : '–'}</tspan></text>`);

  // moving averages
  const maLine = (arr, col, w = 1.6) => {
    const pts = arr.map((v, i) => (v == null ? null : `${x(i)},${y(v)}`)).filter(Boolean).join(' ');
    if (pts) push(`<polyline points="${pts}" fill="none" stroke="${col}" stroke-width="${w}" opacity="0.9"/>`);
  };
  maLine(s200, C.sma200, 2);
  maLine(e55, C.ema55);
  maLine(e21, C.ema21);
  maLine(e8, C.ema8);

  // candles
  candles.forEach((c, i) => {
    const up = c.close >= c.open;
    const col = up ? C.up : C.down;
    const xi = x(i);
    push(`<line x1="${xi}" y1="${y(c.high)}" x2="${xi}" y2="${y(c.low)}" stroke="${col}" stroke-width="1.2"/>`);
    const top = y(Math.max(c.open, c.close));
    const bh = Math.max(1, Math.abs(y(c.open) - y(c.close)));
    // Solid bodies both ways. Hollow up-candles vanish against the dark panel and
    // make every chart read as a selloff regardless of what the tape actually did.
    push(`<rect x="${xi - cw / 2}" y="${top}" width="${cw}" height="${bh}" fill="${col}" stroke="${col}" stroke-width="1.2"/>`);
  });

  // Dealer levels + the last-price tag share one right gutter, and on a tight name
  // the strikes are a dollar apart, so lay them out together and push overlapping
  // tags/labels vertically apart. Lines stay at their true price; only text moves.
  const last = candles[n - 1].close;
  const tags = [
    ...levels.map((l) => ({ ...l, y: y(l.price) })),
    { price: last, color: C.text, y: y(last), isLast: true },
  ].sort((a, b) => a.y - b.y);

  const TAG_H = 23;
  for (let i = 1; i < tags.length; i++) {
    if (tags[i].y - tags[i - 1].y < TAG_H) tags[i].y = tags[i - 1].y + TAG_H;
  }
  const overflow = tags[tags.length - 1].y - (PAD_T + PRICE_H - 4);
  if (overflow > 0) for (const t of tags) t.y -= overflow;

  // Labels stay glued to their own line — nudging them vertically would make them
  // point at the wrong price — so crowded levels get pushed sideways into free space.
  const placed = [];
  const LABEL_H = 17;
  function labelSlot(yy, w) {
    let lx = PAD_L + 12;
    for (let guard = 0; guard < 12; guard++) {
      const hit = placed.find((p) => Math.abs(p.y - yy) < LABEL_H && lx < p.x + p.w && lx + w > p.x);
      if (!hit) break;
      lx = hit.x + hit.w + 16;
    }
    placed.push({ x: lx, y: yy, w });
    return lx;
  }

  for (const t of tags) {
    const yy = y(t.price);
    if (t.isLast) {
      push(`<line x1="${PAD_L}" y1="${yy}" x2="${PAD_L + PLOT_W}" y2="${yy}" stroke="${C.text}" stroke-width="1" stroke-dasharray="3 4" opacity="0.55"/>`);
    } else {
      push(`<line x1="${PAD_L}" y1="${yy}" x2="${PAD_L + PLOT_W}" y2="${yy}" stroke="${t.color}" stroke-width="1.6" opacity="0.85"${t.dash ? ' stroke-dasharray="7 5"' : ''}/>`);
      const lw = t.label.length * 7.05 + 12;
      const lx = labelSlot(yy, lw);
      push(`<rect x="${lx - 6}" y="${yy - 17}" width="${lw}" height="15" rx="2" fill="${C.bg}" opacity="0.85"/>`);
      push(`<text x="${lx}" y="${yy - 5}" fill="${t.color}" font-size="12" opacity="0.98">${esc(t.label)}</text>`);
    }
    // leader from the true price to the nudged tag when they've been pulled apart
    if (Math.abs(t.y - yy) > 1.5) {
      push(`<line x1="${PAD_L + PLOT_W}" y1="${yy}" x2="${PAD_L + PLOT_W + 4}" y2="${t.y}" stroke="${t.color}" stroke-width="1" opacity="0.6"/>`);
    }
    push(`<rect x="${PAD_L + PLOT_W + 4}" y="${t.y - TAG_H / 2}" width="${PAD_R - 14}" height="${TAG_H}" rx="3" fill="${t.color}"/>`);
    push(`<text x="${PAD_L + PLOT_W + 12}" y="${t.y + 5}" fill="#0a0a0e" font-size="13" font-weight="700">${fmt(t.price)}</text>`);
  }

  for (const a of axisLabels) {
    if (tags.some((t) => Math.abs(t.y - a.y) < TAG_H)) continue;
    push(`<text x="${PAD_L + PLOT_W + 12}" y="${a.y + 4}" fill="${C.dim}" font-size="13">${fmt(a.p)}</text>`);
  }

  // x axis dates
  const xStep = Math.max(1, Math.floor(n / 9));
  for (let i = 0; i < n; i += xStep) {
    const d = new Date(candles[i].date);
    const lbl = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    push(`<line x1="${x(i)}" y1="${PAD_T}" x2="${x(i)}" y2="${PAD_T + PRICE_H}" stroke="${C.line}" stroke-dasharray="2 8"/>`);
    push(`<text x="${x(i)}" y="${RSI_T + RSI_H + 22}" fill="${C.dim}" font-size="12" text-anchor="middle">${lbl}</text>`);
  }

  // header
  const chg = meta.changePercent ?? 0;
  const chgCol = chg >= 0 ? C.up : C.down;
  push(`<text x="${PAD_L + 2}" y="40" fill="${C.text}" font-size="30" font-family="Share Tech Mono, monospace" letter-spacing="1.5">${esc(sym)}</text>`);
  push(`<text x="${PAD_L + 2 + sym.length * 20 + 18}" y="40" fill="${C.text}" font-size="24">$${fmt(meta.currentPrice)}</text>`);
  push(`<text x="${PAD_L + 2 + sym.length * 20 + 18 + String(fmt(meta.currentPrice)).length * 14 + 34}" y="40" fill="${chgCol}" font-size="19">${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%</text>`);
  if (meta.name && meta.name !== sym) {
    push(`<text x="${PAD_L + 2}" y="62" fill="${C.dim}" font-size="13">${esc(meta.name)}</text>`);
  }
  if (gex) {
    const pos = (gex.totalGEX || 0) >= 0;
    const rcol = pos ? C.up : C.down;
    push(`<rect x="${W - PAD_R - 470}" y="20" width="470" height="26" rx="13" fill="${pos ? '#0c1a13' : '#1a0e11'}" stroke="${pos ? '#103a26' : '#3a1c22'}"/>`);
    push(`<text x="${W - PAD_R - 452}" y="38" fill="${rcol}" font-size="13">${esc(gex.interpretation?.marketRegime || '')} · flip $${fmt(gex.gammaFlipLevel)} · pin $${fmt(gex.maxGammaStrike)}</text>`);
  }
  // legend
  const leg = [['EMA8', C.ema8], ['EMA21', C.ema21], ['EMA55', C.ema55], ['SMA200', C.sma200]];
  leg.forEach(([t, c], i) => {
    const lx = PAD_L + 12 + i * 96;
    push(`<line x1="${lx}" y1="${PAD_T + 16}" x2="${lx + 18}" y2="${PAD_T + 16}" stroke="${c}" stroke-width="2.4"/>`);
    push(`<text x="${lx + 24}" y="${PAD_T + 20}" fill="${C.dim}" font-size="11.5">${t}</text>`);
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<rect width="${W}" height="${H}" fill="${C.bg}"/>
<g font-family="JetBrains Mono, ui-monospace, monospace">${out.join('\n')}</g>
<text x="${PAD_L + 2}" y="${H - 14}" fill="#4a4a5c" font-size="11">TraderDaddy Pro · dealer levels from live options chain</text>
</svg>`;
}

// ── main ────────────────────────────────────────────────────────────────────
function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i > -1 ? process.argv[i + 1] : def;
}

const symbols = process.argv.slice(2).filter((a) => !a.startsWith('--') && a !== arg('out') && a !== arg('days'));
const outDir = resolve(arg('out', '/tmp/recap_charts'));
// ~4 months of tape: enough trend to read, without squashing recent action into the right edge.
const days = Number(arg('days', 88));
const wantGex = !process.argv.includes('--no-gex');

if (!symbols.length) {
  console.error('usage: node render_chart.mjs SYM [SYM...] --out DIR [--days 88] [--no-gex]');
  process.exit(1);
}
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });

for (const sym of symbols) {
  try {
    const [meta, gex] = await Promise.all([
      fetchCandles(sym, days),
      wantGex ? fetchGex(sym) : Promise.resolve(null),
    ]);
    const svg = buildSvg(sym, meta, meta.chartData, gex);
    await page.setContent(
      `<html><head>
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Share+Tech+Mono&display=swap">
        <style>html,body{margin:0;padding:0;background:${C.bg}}</style>
      </head><body>${svg}</body></html>`,
      { waitUntil: 'networkidle' },
    );
    const out = join(outDir, `${sym}.png`);
    await page.screenshot({ path: out });
    console.log(`${sym}\t${out}`);
  } catch (e) {
    console.error(`${sym}\tERROR ${e.message}`);
  }
}

await browser.close();