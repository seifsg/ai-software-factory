/** Observations for explicit checks; no browser launch or automatic visual verdict. */
export async function rendered(locator) {
  const found = [];
  for (const item of await locator.all()) if (await item.isVisible()) found.push(item);
  return found;
}

/** Responsive copies may share a name, but two rendered matches are ambiguous. */
export async function oneRendered(locator) {
  const matches = await rendered(locator);
  if (matches.length !== 1) throw new Error(`Expected one rendered match; found ${matches.length}`);
  return matches[0];
}

/** Tab from the caller's current position; hidden-before-focus is not a failure. */
export async function keyboardTarget(page, locator, maxTabs = 20) {
  if (!Number.isInteger(maxTabs) || maxTabs < 1 || maxTabs > 100) throw new Error('maxTabs must be 1..100');
  if (await locator.count() !== 1) throw new Error('Keyboard target must be unique');
  for (let tabs = 0; tabs <= maxTabs; tabs++) {
    if (await locator.evaluate(el => el === document.activeElement)) {
      return locator.evaluate((el, tabs) => {
        const r = el.getBoundingClientRect(), s = getComputedStyle(el);
        return { reached: true, tabs, visible: r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0
          && r.top < innerHeight && r.left < innerWidth && s.visibility === 'visible' && Number(s.opacity) > 0
          && s.clipPath === 'none' && s.clip === 'auto' };
      }, tabs);
    }
    if (tabs < maxTabs) await page.keyboard.press('Tab');
  }
  return { reached: false, tabs: maxTabs, visible: null };
}

/** Composite supported solid alpha backgrounds; unknown effects stay unknown. */
export async function background(locator) {
  return locator.evaluate(el => {
    let alpha = 0, rgb = [0, 0, 0];
    for (let item = el; item; item = item.parentElement) {
      const s = getComputedStyle(item);
      if (s.backgroundImage !== 'none' || s.mixBlendMode !== 'normal' || Number(s.opacity) !== 1
          || s.filter !== 'none' || s.backdropFilter !== 'none') return { known: false, reason: 'image, blend, opacity or filter' };
      const m = s.backgroundColor.match(/^rgba?\(([^)]+)\)$/);
      if (!m) return { known: false, reason: `unsupported color ${s.backgroundColor}` };
      const parts = m[1].split(/[,\s/]+/).filter(Boolean).map(Number), a = parts.length === 4 ? parts[3] : 1;
      if (parts.some(n => !Number.isFinite(n))) return { known: false, reason: 'unsupported color components' };
      rgb = rgb.map((n, i) => n + parts[i] * a * (1 - alpha));
      alpha += a * (1 - alpha);
      // An opaque child can still be composited by an ancestor effect.
    }
    return alpha >= 1 - 1e-6 ? { known: true, rgb: rgb.map(Math.round) }
      : { known: false, reason: 'no opaque ancestor; canvas background unspecified' };
  });
}

/** A mask or pseudo-element can draw an icon without any background image. */
export async function iconPaint(locator) {
  return locator.evaluate(el => ['', '::before', '::after'].map(pseudo => {
    const s = getComputedStyle(el, pseudo || null);
    return { pseudo: pseudo || 'element', content: s.content, mask: s.maskImage || s.webkitMaskImage,
      background: s.backgroundImage, color: s.color, backgroundColor: s.backgroundColor };
  }));
}
