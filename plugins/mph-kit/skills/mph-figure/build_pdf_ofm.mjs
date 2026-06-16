// Merge all xhtml chapters into one doc + render to PDF via Playwright.
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const OFM_ROOT = 'C:/Users/mphan/.ofm-build';
const TEXT_DIR = join(OFM_ROOT, 'EPUB', 'text');
const CSS_PATH = join(OFM_ROOT, 'EPUB', 'styles', 'stylesheet1.css');
const OUT_HTML = join(TEXT_DIR, '_merged.html');
const OUT_PDF = 'C:/Users/mphan/OneDrive/Documents/GitHub/mphinance/The_Options_Field_Manual_v2.pdf';

// Spine order (matches content.opf)
const SPINE = [
  'cover.xhtml', 'title_page.xhtml',
  'ch001.xhtml', 'ch002.xhtml', 'ch003.xhtml',
  'ch004.xhtml', 'ch005.xhtml', 'ch006.xhtml',
  'ch007.xhtml', 'ch008.xhtml', 'ch009.xhtml',
  'ch010.xhtml', 'ch011.xhtml', 'ch012.xhtml',
  'ch013.xhtml', 'ch014.xhtml', 'ch015.xhtml',
  'ch016.xhtml', 'ch017.xhtml', 'ch018.xhtml',
  'ch019.xhtml',
];

// Extract <body>...</body> contents from each chapter
function bodyOf(xhtml) {
  const m = xhtml.match(/<body[^>]*>([\s\S]*?)<\/body>/);
  return m ? m[1] : '';
}

const css = readFileSync(CSS_PATH, 'utf8');
const parts = SPINE.map(f => bodyOf(readFileSync(join(TEXT_DIR, f), 'utf8')));

// Add page-break-before:always to each section's <section> opener except the first
const body = parts.map((p, i) => {
  if (i === 0) return p;
  return p.replace(/<section /, '<section style="page-break-before: always;" ');
}).join('\n');

const merged = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>The Options Field Manual</title>
<style>
${css}
@page { margin: 1.5cm 1.8cm; size: letter; }
body { font-family: Georgia, serif; line-height: 1.5; color: #1a1a1a; max-width: none; }
section { padding: 0; }
img { max-width: 100%; }
.fig img { max-width: 90%; }
h1 { font-size: 26px; margin: 0 0 18px; }
h3 { font-size: 18px; margin: 22px 0 10px; }
p { margin: 0.8em 0; }
.sam-sidebar { page-break-inside: avoid; }
table { page-break-inside: avoid; }
</style>
</head>
<body>
${body}
</body>
</html>`;

writeFileSync(OUT_HTML, merged, 'utf8');
console.log(`merged html written (${merged.length} chars)`);

const browser = await chromium.launch();
const page = await browser.newPage();
const fileUrl = 'file:///' + OUT_HTML.replace(/\\/g, '/');
console.log(`loading ${fileUrl}`);
await page.goto(fileUrl, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(500);
await page.pdf({
  path: OUT_PDF,
  format: 'Letter',
  printBackground: true,
  margin: { top: '1.5cm', bottom: '1.5cm', left: '1.8cm', right: '1.8cm' },
});
await browser.close();
console.log(`pdf written: ${OUT_PDF}`);
