const { chromium } = require('playwright');
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];

  let vp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('vercel.com') && p.url().includes('quickquote')) { vp = p; break; }
  }
  if (!vp) { console.log('No vercel tab'); return; }

  await vp.goto('https://vercel.com/markyuan-jpgs-projects/quickquote/settings/environment-variables', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(5000);

  // Click Add Environment Variable
  await vp.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      if (b.textContent.trim().includes('Add Environment')) { b.click(); return; }
    }
  });
  await sleep(2000);

  // Fill key (get the blank text input before the textarea)
  await vp.evaluate(() => {
    const inputs = document.querySelectorAll('input[type="text"]');
    // Find the blank one (not search, not combobox, not comment)
    for (const inp of inputs) {
      const ph = inp.getAttribute('placeholder') || '';
      const id = inp.id || '';
      const value = inp.value || '';
      if (!ph && !id.includes('combobox') && !id.includes('search') && !ph.includes('Where') && id !== '') {
        inp.focus();
        inp.value = '';
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        inp.value = 'NEXT_PUBLIC_API_URL';
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        inp.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('Filled key input:', id);
        return 'filled ' + id;
      }
    }
    return 'not found';
  });
  await sleep(500);

  // Fill value (textarea)
  await vp.evaluate(() => {
    const textareas = document.querySelectorAll('textarea');
    for (const ta of textareas) {
      if (!ta.value) {  // empty textarea
        ta.focus();
        ta.value = 'https://product-tool-production.up.railway.app';
        ta.dispatchEvent(new Event('input', { bubbles: true }));
        ta.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('Filled textarea');
        return 'filled';
      }
    }
    return 'not found';
  });
  await sleep(500);

  // Click Save/Add button - look for the submit button
  await vp.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      const text = b.textContent.replace(/\s+/g, ' ').trim();
      if (text === 'Add' || text === 'Save' || text === 'Create' || text.includes('Add Environment')) {
        if (b.getAttribute('type') === 'submit' || !b.getAttribute('type') || !b.disabled) {
          b.click();
          return 'clicked ' + text;
        }
      }
    }
    return 'not found';
  });
  await sleep(3000);

  // Verify
  const text = await vp.evaluate(() => document.body.innerText);
  const apiLines = text.split('\n').filter(l => l.includes('API_URL') || l.includes('NEXT_PUBLIC'));
  console.log('After save:', apiLines);

  await vp.screenshot({ path: '_vercel_done.png' });
  console.log('DONE');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
