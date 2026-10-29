#!/usr/bin/env node
// Optional browser calibration stays outside the Python rubric protocol.
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const {variants, html} = require('./fixtures.cjs');
const {observe} = require('./checks.cjs');

function options(argv) {
  const result = {out: '.factory/evals/visual', repeat: 1, expected: path.join(__dirname, 'expected.json')};
  for (let i = 0; i < argv.length; i += 2) {
    const flag = argv[i], value = argv[i + 1];
    if (!['--out', '--repeat', '--expected', '--browser'].includes(flag) || !value) throw new Error(`Invalid argument: ${flag}`);
    result[flag.slice(2)] = value;
  }
  result.repeat = Number(result.repeat);
  if (!Number.isInteger(result.repeat) || result.repeat < 1 || result.repeat > 20) throw new Error('repeat must be 1..20');
  return result;
}

const hash = text => crypto.createHash('sha256').update(text).digest('hex');
const viewports = [{width: 1280, height: 800}, {width: 390, height: 844}];

async function run(config) {
  await fs.mkdir(config.out, {recursive: true});
  const report = {version: 1, kind: 'objective-rendered-calibration', viewports, trials: [], passed: false};
  let browser, server;
  try {
    const expected = JSON.parse(await fs.readFile(config.expected, 'utf8'));
    if (JSON.stringify(Object.keys(expected).sort()) !== JSON.stringify([...variants].sort()) ||
        Object.values(expected).some(ids => !Array.isArray(ids) || new Set(ids).size !== ids.length ||
          ids.some(id => !['R1', 'R2', 'R3', 'R4'].includes(id)))) throw new Error('Invalid expected labels');
    report.checker = hash(await fs.readFile(path.join(__dirname, 'checks.cjs')));
    report.labels = hash(await fs.readFile(config.expected));
    const {chromium} = require('playwright');
    browser = await chromium.launch({headless: true, timeout: 15000,
      ...(config.browser ? {executablePath: config.browser} : {})});
    report.browser = {engine: 'chromium', version: browser.version(),
      executable: config.browser || chromium.executablePath()};
    const candidates = Object.fromEntries(variants.map(name => [`/${name}`, html(name)]));
    server = http.createServer((request, response) => {
      const source = candidates[request.url];
      response.writeHead(source ? 200 : 404, {'Content-Type': 'text/html; charset=utf-8'});
      response.end(source || 'Not found');
    });
    await new Promise((resolve, reject) => {server.once('error', reject); server.listen(0, '127.0.0.1', resolve);});
    const origin = `http://127.0.0.1:${server.address().port}`;
    report.origin = origin;
    for (let repeat = 1; repeat <= config.repeat; repeat++) {
      for (const name of variants) {
        const candidateFile = `${name}.html`;
        await fs.writeFile(path.join(config.out, candidateFile), candidates[`/${name}`]);
        const trial = {name, repeat, candidateFile, candidate: hash(candidates[`/${name}`]), views: []};
        for (const viewport of viewports) {
          const context = await browser.newContext({viewport, reducedMotion: 'reduce', locale: 'en-US'});
          try {
            const page = await context.newPage();
            page.setDefaultTimeout(5000);
            const errors = [];
            page.on('pageerror', error => errors.push(error.message));
            await page.goto(`${origin}/${name}`, {waitUntil: 'load', timeout: 5000});
            await page.evaluate(() => document.fonts.ready);
            const screenshot = `${name}-${repeat}-${viewport.width}.png`;
            await page.screenshot({path: path.join(config.out, screenshot), fullPage: true, timeout: 5000});
            const criteria = await observe(page);
            if (errors.length) throw new Error(`Page error: ${errors.join('; ')}`);
            const image = await fs.readFile(path.join(config.out, screenshot));
            trial.views.push({viewport, criteria, screenshot, screenshotHash: hash(image)});
          } finally {await context.close();}
        }
        trial.failed = ['R1', 'R2', 'R3', 'R4'].filter(id => trial.views.some(view => !view.criteria[id].pass));
        trial.accepted = trial.failed.length === 0;
        trial.expectedFailures = expected[name];
        trial.calibrated = JSON.stringify(trial.failed) === JSON.stringify([...expected[name]].sort());
        report.trials.push(trial);
        console.log(`${name} #${repeat}: ${trial.accepted ? 'ACCEPT' : `REJECT ${trial.failed.join(',')}`} calibration=${trial.calibrated ? 'PASS' : 'FAIL'}`);
      }
    }
    report.passed = report.trials.every(trial => trial.calibrated);
  } catch (error) {
    report.error = error.message;
  } finally {
    const cleanup = await Promise.allSettled([
      browser ? browser.close() : Promise.resolve(),
      server ? new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve())) : Promise.resolve(),
    ]);
    const failures = cleanup.filter(result => result.status === 'rejected');
    if (failures.length) {
      report.error = `Cleanup failed: ${failures.map(result => result.reason.message).join('; ')}`;
      report.passed = false;
    }
    await fs.writeFile(path.join(config.out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  }
  if (report.error) console.error(report.error);
  return report.passed ? 0 : 1;
}

if (require.main === module) {
  Promise.resolve().then(() => run(options(process.argv.slice(2))))
    .then(code => {process.exitCode = code;}, error => {console.error(error.message); process.exitCode = 2;});
}
module.exports = {options, run};
