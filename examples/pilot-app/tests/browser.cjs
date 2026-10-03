const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require(process.env.SAFE_PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const root = process.cwd();
  const output = path.join(root, '.factory', 'outputs', 'browser');
  await fs.mkdir(output, {recursive:true});
  const files = {'/':'index.html','/style.css':'style.css','/app.js':'app.js','/model.mjs':'model.mjs'};
  const server = http.createServer(async (request, response) => {
    const file = files[request.url];
    if (!file) { response.writeHead(404); response.end(); return; }
    try {
      const type = file.endsWith('.css') ? 'text/css' : /\.(js|mjs)$/.test(file) ? 'text/javascript' : 'text/html';
      response.writeHead(200, {'Content-Type':type, 'Cache-Control':'no-store'});
      response.end(await fs.readFile(path.join(root,file)));
    } catch (error) { response.writeHead(500); response.end('Fixture file unavailable'); }
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  let browser;
  try {
    browser = await chromium.launch({headless:true, ...(process.env.SAFE_BROWSER_EXECUTABLE ? {executablePath:process.env.SAFE_BROWSER_EXECUTABLE} : {})});
    const context = await browser.newContext({viewport:{width:320,height:740}});
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'Mobile page overflows horizontally');
    const button = await page.getByRole('button',{name:'Add task'}).boundingBox();
    assert.ok(button && button.x >= 0 && button.x + button.width <= 320, 'Primary action must fit on screen');
    await page.getByLabel('What needs doing?').fill('   ');
    await page.getByRole('button',{name:'Add task'}).click();
    assert.equal(await page.getByRole('status').textContent(), 'Enter a task title.');
    assert.equal(await page.getByRole('listitem').count(),0);
    await page.getByLabel('What needs doing?').fill('  Review the feature  ');
    await page.getByLabel('What needs doing?').press('Enter');
    assert.equal(await page.getByRole('listitem').textContent(),'Review the feature');
    assert.equal(await page.getByRole('status').textContent(),'Task added.');
    await page.reload();
    await page.getByRole('listitem').waitFor();
    assert.equal(await page.getByRole('listitem').textContent(),'Review the feature');
    await page.screenshot({path:path.join(output,'mobile-complete.png'),fullPage:true});
    await page.setViewportSize({width:1440,height:900});
    await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.deepEqual(pageErrors,[]);
    await context.close();
    console.log('PASS: mobile layout, blank-title rejection, keyboard submission, feedback, reload persistence, desktop, no page errors');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error);process.exitCode=1;});
