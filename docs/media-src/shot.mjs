// Render an HTML file to a PNG with a headless browser.
// Usage: node shot.mjs page.html out.png [width=1100] [height=0 (0 = full page)] [scale=2]
// Resolves `playwright` from node_modules next to this file or from NODE_PATH.
import { createRequire } from 'node:module';
import path from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright');

const [, , html, out, w = '1100', h = '0', s = '2'] = process.argv;
if (!html || !out) {
  console.error('usage: node shot.mjs page.html out.png [width] [height] [scale]');
  process.exit(2);
}
const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: Number(w), height: Number(h) || 200 },
  deviceScaleFactor: Number(s),
});
await page.goto('file://' + path.resolve(html));
await page.screenshot({ path: out, fullPage: Number(h) === 0 });
await browser.close();
console.log('wrote', out);
