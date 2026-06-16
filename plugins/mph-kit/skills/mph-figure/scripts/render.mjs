#!/usr/bin/env node
// mph-figure - render markdown (or HTML) into a crisp, themed PNG.
//
// Usage:
//   node render.mjs --in <file.md|file.html> --out <file.png> [options]
//
// Options:
//   --width <px>    figure width             (default 720)
//   --scale <n>     device scale / sharpness (default 2)
//   --theme <name>  visual theme             (default bloomberg)
//   --html          treat --in as raw HTML regardless of extension

import { chromium } from 'playwright';
import { readFileSync } from 'fs';
import { extname } from 'path';
import MarkdownIt from 'markdown-it';

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i > -1 ? process.argv[i + 1] : def;
}

const BASE = `
  * { box-sizing:border-box; margin:0; padding:0; }
  html,body { background:transparent; }
`;

const THEMES = {
  // Dark, data-first, "Bloomberg terminal" look.
  bloomberg: `
    .figure { background:#0c0f17; color:#e7eaf3; border:1px solid #232838;
      border-radius:14px; padding:26px 28px;
      font-family:'Inter',system-ui,-apple-system,sans-serif;
      font-size:15px; line-height:1.6; }
    .figure :where(h1,h2,h3,h4) { font-weight:700; line-height:1.25;
      margin:0 0 10px; color:#ffffff; letter-spacing:-0.01em; }
    .figure h1 { font-size:26px; }
    .figure h2 { font-size:21px; }
    .figure h3 { font-size:17px; }
    .figure p { margin:0 0 10px; color:#c4c9da; }
    .figure > *:last-child { margin-bottom:0; }
    .figure strong { color:#ffffff; font-weight:600; }
    .figure em { color:#dfe3ef; }
    .figure a { color:#ff9e2c; }
    .figure ul, .figure ol { margin:0 0 10px; padding-left:22px; color:#c4c9da; }
    .figure li { margin-bottom:3px; }
    .figure code { font-family:ui-monospace,'Cascadia Code',Consolas,monospace;
      background:#1a1f2e; padding:1px 6px; border-radius:5px; font-size:0.88em;
      color:#ffd9a6; }
    .figure pre { background:#070a10; border:1px solid #232838; border-radius:10px;
      padding:14px 16px; overflow:auto; margin:0 0 10px; }
    .figure pre code { background:none; padding:0; color:#e7eaf3; }
    .figure blockquote { border-left:3px solid #ff9e2c; padding-left:14px;
      margin:0 0 10px; color:#9aa1b8; }
    .figure hr { border:none; border-top:1px solid #232838; margin:16px 0; }
    .figure table { width:100%; border-collapse:collapse; margin:0 0 10px;
      font-variant-numeric:tabular-nums; }
    .figure thead th { background:#161b29; color:#ff9e2c; text-align:left;
      font-weight:600; font-size:12px; text-transform:uppercase;
      letter-spacing:0.06em; padding:10px 13px; border-bottom:2px solid #2a3043; }
    .figure tbody td { padding:9px 13px; border-bottom:1px solid #1c2130;
      color:#dfe3ef; }
    .figure tbody tr:nth-child(even) { background:#11141f; }
    .figure tbody tr:last-child td { border-bottom:none; }
  `
};

async function main() {
  const inPath = arg('in');
  const outPath = arg('out');
  if (!inPath || !outPath) {
    console.error('mph-figure: need --in <file.md|file.html> and --out <file.png>');
    process.exit(1);
  }
  const width = parseInt(arg('width', '720'), 10);
  const scale = parseFloat(arg('scale', '2'));
  const themeName = arg('theme', 'bloomberg');
  const theme = THEMES[themeName] || THEMES.bloomberg;

  const raw = readFileSync(inPath, 'utf8');
  const isHtml = process.argv.includes('--html') ||
                 extname(inPath).toLowerCase() === '.html';
  const body = isHtml
    ? raw
    : new MarkdownIt({ html: true, linkify: true }).render(raw);

  const doc = `<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>${BASE}${theme}#figure{width:${width}px;}</style></head>
<body><div id="figure" class="figure">${body}</div></body></html>`;

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ deviceScaleFactor: scale });
    await page.setViewportSize({ width: width + 140, height: 900 });
    await page.setContent(doc, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.locator('#figure').screenshot({ path: outPath, omitBackground: true });
    console.log(`mph-figure: wrote ${outPath}`);
  } finally {
    await browser.close();
  }
}

main().catch((e) => { console.error('mph-figure: ' + e.message); process.exit(1); });
