import { createRequire } from 'node:module';
import { strict as assert } from 'node:assert';
import { oneRendered, keyboardTarget, background, iconPaint } from '../skills/safe-engine/scripts/playwright_checks.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('@playwright/test');
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  for (const width of [1280, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 844 } });
    await page.setContent(`<style>
      body { background: white }
      .phone { display: none }
      @media(max-width:600px) { .phone { display: block } .desktop { display: none } }
      .skip { position: absolute; left: -9999px }
      .skip:focus { left: 8px; top: 8px }
      .under { background: rgb(20, 40, 60) }
      .over { background: rgba(100, 120, 140, .5) }
      .effect { filter: opacity(.5) }
      .icon { width: 24px; height: 24px; background: red; mask-image: linear-gradient(black,black) }
    </style><a class=skip href=#main>Skip to records</a><main id=main>
      <button class=desktop>Export records</button><button class=phone>Export records</button>
      <div class=under><div class=over><span id=alpha>Summary</span></div></div>
      <div class=effect><span id=effect>Effect</span></div><div class=icon></div></main>`);
    const buttons = page.getByRole('button', { name: 'Export records', exact: true, includeHidden: true });
    const chosen = await oneRendered(buttons);
    assert.equal(await chosen.getAttribute('class'), width === 390 ? 'phone' : 'desktop');
    const skip = await keyboardTarget(page, page.getByRole('link', { name: 'Skip to records' }));
    assert.equal(skip.reached && skip.visible, true);
    assert.deepEqual(await background(page.locator('#alpha')), { known: true, rgb: [60, 80, 100] });
    assert.equal((await background(page.locator('#effect'))).known, false);
    assert.match((await iconPaint(page.locator('.icon')))[0].mask, /gradient/);
    await page.locator('.phone').evaluate(el => { el.style.display = 'block'; });
    if (width === 1280) await assert.rejects(oneRendered(buttons), /found 2/);
    await page.close();
  }
  console.log('browser helpers: desktop, phone, focus, alpha, unsupported effect, mask, duplicate PASS');
} finally {
  await browser.close();
}
