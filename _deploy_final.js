const { chromium } = require('playwright');
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];

  let rp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('railway.com')) { rp = p; break; }
  }
  if (!rp) { rp = await ctx.newPage(); }

  // ─── Step 1: Service Settings ───
  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f/service/1ef412c7-16bf-487c-b8a1-3cd5cd753b69/settings', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(5000);

  // Click Generate Domain button
  await rp.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      if (b.textContent.trim() === 'Generate Domain') { b.click(); return; }
    }
  });
  await sleep(2000);

  // Check dialog elements
  const dialogInfo = await rp.evaluate(() => {
    const all = document.querySelectorAll('select, input, button, [role="combobox"], [role="listbox"]');
    return Array.from(all).map(el => ({
      tag: el.tagName,
      type: el.getAttribute('type') || '',
      role: el.getAttribute('role') || '',
      text: el.textContent.trim().substring(0, 40),
      placeholder: el.getAttribute('placeholder') || '',
      ariaLabel: el.getAttribute('aria-label') || '',
    }));
  });
  console.log('Dialog elements:', JSON.stringify(dialogInfo, null, 2));

  // Try clicking select or combobox
  await rp.evaluate(() => {
    // Find select elements
    const sel = document.querySelector('select');
    if (sel) {
      sel.value = '8080';
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      return 'select-filled';
    }
    // Find any element that looks like a port selector
    const els = document.querySelectorAll('[role="combobox"], [role="listbox"], .port-selector');
    for (const e of els) {
      if (e.textContent.includes('port') || e.textContent.includes('Port') || e.getAttribute('aria-label')?.includes('port') || e.getAttribute('aria-label')?.includes('Port')) {
        e.click();
        return 'clicked-combobox';
      }
    }
    return 'nothing-found';
  });
  await sleep(1000);

  // After selecting, click the dialog's Generate Domain button
  const genBtns = await rp.$$('button');
  // Click the LAST Generate Domain (the one in the dialog)
  for (let i = genBtns.length - 1; i >= 0; i--) {
    const t = ((await genBtns[i].textContent()) || '').trim();
    if (t === 'Generate Domain') {
      await genBtns[i].click();
      console.log('Clicked dialog Generate Domain');
      await sleep(5000);
      break;
    }
  }

  const text = await rp.evaluate(() => document.body.innerText);
  // Check for domain
  const domain = text.match(/https?:\/\/[^\s"'<>]*\.up\.railway[^\s"'<>]*/g);
  if (domain) {
    console.log('GENERATED DOMAIN:', domain[0]);
  } else {
    console.log('No domain found yet. Page text:', text.substring(0, 3000));
  }

  await rp.screenshot({ path: '_final.png' });
  console.log('DONE');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
