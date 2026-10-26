/** Lint only journey files declared by a project; ambiguous construction needs review. */
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

/** Reject lexical uncertainty rather than hide executable time reads. */
function unsupported(offset, reason) {
  throw new Error(`clock lint needs manual review at offset ${offset}: ${reason}; simplify this expression and rerun`);
}

/** Find a quoted string or ordinary regex end without interpreting its contents. */
function literalEnd(source, start) {
  const quote = source[start], regex = quote === '/';
  let inClass = false;
  for (let i = start + 1; i < source.length; i++) {
    const c = source[i];
    if (c === '\\') {
      if (regex && /[\r\n\u2028\u2029]/.test(source[i + 1] || '')) break;
      i += source[i + 1] === '\r' && source[i + 2] === '\n' ? 2 : 1;
      continue;
    }
    if (/[\r\n\u2028\u2029]/.test(c)) break;
    if (regex && c === '[') {
      if (inClass) unsupported(i, 'nested regex character class');
      inClass = true;
    } else if (regex && c === ']') inClass = false;
    else if (c === quote && !inClass) {
      let end = i + 1;
      if (regex) {
        while (end < source.length && /[a-z]/i.test(source[end])) end++;
        if (source.slice(i + 1, end).includes('v')) unsupported(start, 'regex Unicode sets');
      }
      return end;
    }
  }
  unsupported(start, 'unterminated string or regex');
}

/** Keep two offset-aligned views in one scan; this is not a JavaScript parser. */
function executableText(source) {
  const bare = source.split(''), code = source.split('');
  let operand = true, property = false, template = false, depth = -1, lineBreak = false;
  for (let i = 0; i < source.length;) {
    const start = i, c = source[i], next = source[i + 1];
    if (template) {
      i += c === '\\' || (c === '$' && next === '{') ? 2 : 1;
      bare.fill(' ', start, i);
      if (c === '$' && next === '{') { template = false; depth = 0; operand = true; property = false; }
      else if (c === '`') { template = false; operand = false; }
      continue;
    }
    if (/\s/.test(c)) { lineBreak ||= /[\r\n\u2028\u2029]/.test(c); i++; continue; }
    if (c === '/' && (next === '/' || next === '*')) {
      i += 2;
      if (next === '/') while (i < source.length && !/[\r\n\u2028\u2029]/.test(source[i])) i++;
      else {
        const end = source.indexOf('*/', i);
        if (end < 0) unsupported(start, 'unterminated comment');
        i = end + 2;
      }
      lineBreak ||= /[\r\n\u2028\u2029]/.test(source.slice(start, i));
      bare.fill(' ', start, i); code.fill(' ', start, i); continue;
    }
    if (c === '/' && (operand === null || (!operand && lineBreak))) unsupported(i, 'ambiguous regex or division');
    lineBreak = false;
    if (c === '"' || c === "'" || (c === '/' && operand)) {
      i = literalEnd(source, i); bare.fill(' ', start, i); operand = false; property = false; continue;
    }
    if (c === '`') {
      if (depth >= 0) unsupported(i, 'nested template expression');
      bare[i++] = ' '; template = true; property = false; continue;
    }
    if (/[a-z_$]/i.test(c)) {
      while (i < source.length && /[\w$]/.test(source[i])) i++;
      const word = source.slice(start, i);
      operand = !property && /^(return|throw|case|default|delete|void|typeof|new|in|instanceof|else|do)$/.test(word);
      if (!property && /^(await|yield|of|async|break|continue|debugger|import|export|extends|const|let|var|function|class|switch|if|while|for|try|catch|finally|with)$/.test(word)) operand = null;
      property = false; continue;
    }
    if (/\d/.test(c)) {
      while (i < source.length && /[\w.]/.test(source[i])) i++;
      operand = false; property = false; continue;
    }
    if (c === '{' && depth >= 0) depth++;
    if (c === '}' && depth >= 0 && depth-- === 0) {
      bare[i++] = ' '; template = true; continue;
    }
    if (!'(){}[];,:.?~!+-*/%&|^<=>'.includes(c)) unsupported(i, 'unsupported code token');
    // Closing statements and postfix operators need grammar to disambiguate a slash.
    operand = c === ')' || c === '}' ? null : c !== ']' && c !== '.';
    if ((c === '+' || c === '-') && next === c) { i++; operand = null; }
    property = c === '.'; i++;
  }
  if (template || depth >= 0) unsupported(source.length, 'unterminated template expression');
  return { bare: bare.join(''), code: code.join('') };
}

function inspect(source) {
  let code, bare;
  try { ({ code, bare } = executableText(source)); }
  catch (error) { return [error.message]; }
  const findings = [];
  if (!/\bfixedBrowserPage\s*\(/.test(bare)) findings.push('missing fixedBrowserPage fixture');
  if (/\bDate\s*\.\s*now\s*\(/.test(bare)) findings.push('real-time Date.now()');
  for (const match of bare.matchAll(/\bnew\s+Date\s*\(/g)) {
    const end = bare.indexOf(')', match.index + match[0].length);
    if (end < 0) { findings.push('unsupported Date construction'); continue; }
    const args = code.slice(match.index + match[0].length, end).trim();
    if (!args) findings.push('real-time new Date()');
    else if (!/^(?:['"]\d{4}-\d\d-\d\d(?:T[^'"]+)?['"]|\d{4}\s*,\s*\d{1,2}(?:\s*,\s*\d{1,2}(?:\s*,\s*\d{1,2}(?:\s*,\s*\d{1,2}(?:\s*,\s*\d{1,2})?)?)?)?)$/.test(args))
      findings.push(`unsupported Date construction: ${args.slice(0, 80)}`);
  }
  if (/\b(?:Date\s*\[|globalThis\s*\[|eval\s*\(|Function\s*\()/.test(bare))
    findings.push('dynamic time access needs manual review');
  return findings;
}

export function lintJourneyClock(manifestPath) {
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  if (manifest.version !== 1 || !Array.isArray(manifest.journey_tests) || !manifest.journey_tests.length)
    throw new Error('manifest must declare nonempty journey_tests, version 1');
  const root = dirname(resolve(manifestPath));
  return manifest.journey_tests.flatMap(file => {
    if (typeof file !== 'string' || !file.trim() || file.startsWith('/') || file.includes('..') || /^[A-Za-z]:/.test(file))
      throw new Error(`invalid journey test path: ${file}`);
    return inspect(readFileSync(resolve(root, file), 'utf8')).map(reason => `${file}: ${reason}`);
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.length !== 3) throw new Error('usage: node journey_clock_lint.mjs <manifest.json>');
    const findings = lintJourneyClock(process.argv[2]);
    for (const finding of findings) console.error(finding);
    if (findings.length) process.exitCode = 1;
    else console.log('Journey clock lint PASS');
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
