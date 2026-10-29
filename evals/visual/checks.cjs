// Observe a rendered candidate without its fixture name or expected verdict.
async function observe(page) {
  const geometry = await page.evaluate(() => {
    const headings = ['Welcome', 'Learn', 'Progress', 'Contact'];
    // Every text fragment must fit its section, viewport width and clipping ancestors.
    function visible(node, section) {
      const range = document.createRange();
      range.selectNodeContents(node);
      const fragments = [...range.getClientRects()].filter(box => box.width > 0 && box.height > 0)
        .map(box => ({left: box.left, right: box.right, top: box.top, bottom: box.bottom}));
      const inside = (box, bounds, x = true, y = true) =>
        (!x || box.left >= bounds.left - 1 && box.right <= bounds.right + 1) &&
        (!y || box.top >= bounds.top - 1 && box.bottom <= bounds.bottom + 1);
      let shown = fragments.length > 0 && fragments.every(box => inside(box, section) &&
        inside(box, {left: 0, right: innerWidth}, true, false));
      for (let element = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
        element; element = element.parentElement) {
        const style = getComputedStyle(element);
        shown &&= style.display !== 'none' && style.visibility === 'visible' && Number(style.opacity) > 0;
        if (element !== document.scrollingElement) {
          const clips = value => ['hidden', 'clip', 'auto', 'scroll'].includes(value);
          const box = element.getBoundingClientRect();
          const bounds = {left: box.left + element.clientLeft, top: box.top + element.clientTop};
          bounds.right = bounds.left + element.clientWidth;
          bounds.bottom = bounds.top + element.clientHeight;
          shown &&= fragments.every(fragment => inside(fragment, bounds, clips(style.overflowX), clips(style.overflowY)));
        }
      }
      return {visible: shown, fragments};
    }
    const rows = headings.map(title => {
      const heading = [...document.querySelectorAll('h2')].find(node => node.textContent.trim() === title);
      const element = heading?.closest('section');
      if (!element) return {title, visible: false, box: null};
      const box = element.getBoundingClientRect();
      const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
      const content = [], headingContent = [];
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        if (node.textContent.trim()) (heading.contains(node) ? headingContent : content)
          .push({text: node.textContent.trim(), ...visible(node, box)});
      }
      const headingVisible = headingContent.length > 0 && headingContent.every(row => row.visible);
      return {title, visible: headingVisible && content.length > 0 && content.every(row => row.visible),
        headingVisible, headingContent, content, box: {x: box.x, y: box.y, width: box.width, height: box.height}};
    });
    return {width: innerWidth, scrollWidth: document.documentElement.scrollWidth, rows};
  });
  const boxes = geometry.rows.filter(row => row.box && row.box.height > 0).map(row => row.box);
  const layout = geometry.scrollWidth <= geometry.width + 1 && boxes.every((box, index) =>
    box.x >= 0 && box.x + box.width <= geometry.width + 1 && box.width >= geometry.width * 0.65 &&
    box.height >= 100 && (!index || box.y >= boxes[index - 1].y + boxes[index - 1].height));
  const before = await page.locator('#result').innerText();
  await page.getByRole('button', {name: 'Complete lesson', exact: true}).click();
  const after = await page.locator('#result').innerText();
  await page.reload({waitUntil: 'load'});
  const restored = await page.locator('#result').innerText();
  return {
    R1: {pass: geometry.rows.every(row => row.visible), observed: geometry.rows},
    R2: {pass: layout, observed: geometry},
    R3: {pass: before === 'Not completed' && after === 'Completed', observed: {before, after}},
    R4: {pass: restored === 'Completed', observed: {restored}},
  };
}

module.exports = {observe};
