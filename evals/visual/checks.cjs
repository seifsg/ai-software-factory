// Observe a rendered candidate without its fixture name or expected verdict.
async function observe(page) {
  const geometry = await page.evaluate(() => {
    const headings = ['Welcome', 'Learn', 'Progress', 'Contact'];
    // Text needs painted bounds and visible ancestors, not merely a visible container.
    function visible(node) {
      const range = document.createRange();
      range.selectNodeContents(node);
      const box = range.getBoundingClientRect();
      if (!box.width || !box.height) return false;
      for (let element = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
        element; element = element.parentElement) {
        const style = getComputedStyle(element);
        if (style.display === 'none' || style.visibility !== 'visible' || Number(style.opacity) === 0) return false;
      }
      return true;
    }
    const rows = headings.map(title => {
      const heading = [...document.querySelectorAll('h2')].find(node => node.textContent.trim() === title);
      const element = heading?.closest('section');
      if (!element) return {title, visible: false, box: null};
      const box = element.getBoundingClientRect();
      const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
      const content = [];
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        if (node.textContent.trim() && !heading.contains(node)) content.push({text: node.textContent.trim(), visible: visible(node)});
      }
      const headingVisible = visible(heading);
      return {title, visible: headingVisible && content.length > 0 && content.every(row => row.visible),
        headingVisible, content, box: {x: box.x, y: box.y, width: box.width, height: box.height}};
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
