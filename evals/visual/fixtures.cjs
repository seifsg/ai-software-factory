// Synthetic candidates isolate omissions, geometry and interaction defects.
const variants = ['reference', 'alternative', 'missing-section', 'hidden-section', 'hidden-content', 'missing-content',
  'mobile-overflow', 'lost-progress', 'dead-button'];

function html(variant) {
  if (!variants.includes(variant)) throw new Error(`Unknown candidate: ${variant}`);
  const sections = [
    ['hero', 'Welcome', 'Learn one useful thing every day.'],
    ['learn', 'Learn', 'Choose a short lesson and try it.'],
    ['progress', 'Progress', '<button id="complete">Complete lesson</button><p id="result">Not completed</p>'],
    ['contact', 'Contact', 'Find the next lesson here.'],
  ].filter(([id]) => variant !== 'missing-section' || id !== 'learn');
  return `<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Learning page</title>
<style>
*{box-sizing:border-box}body{margin:0;font:18px system-ui;background:#f4f1eb;color:#202020}
main{width:min(92%,960px);margin:24px auto;display:grid;gap:20px}
section{min-height:160px;padding:24px;border:2px solid #202020;background:white}
h2{margin:0 0 16px}button{font:inherit;padding:12px;cursor:pointer}
${variant === 'alternative' ? 'main{max-width:880px;gap:28px}section{border-radius:16px;background:#fffef9}' : ''}
${variant === 'hidden-section' ? '#learn{opacity:0}' : ''}
${variant === 'hidden-content' ? '#learn h2,#learn div{opacity:0}' : ''}
${variant === 'mobile-overflow' ? '@media(max-width:600px){main{width:1000px}}' : ''}
</style><main>${sections.map(([id, title, text]) =>
    `<section id="${id}"><h2>${title}</h2><div>${variant === 'missing-content' && id === 'learn' ? '' : text}</div></section>`).join('')}</main>
<script>
const result=document.querySelector('#result');
if(localStorage.getItem('complete')==='yes') result.textContent='Completed';
document.querySelector('#complete').onclick=()=>{
${variant === 'dead-button' ? '' : "result.textContent='Completed';"}
${['dead-button', 'lost-progress'].includes(variant) ? '' : "localStorage.setItem('complete','yes');"}
};
</script></html>`;
}

module.exports = {variants, html};
