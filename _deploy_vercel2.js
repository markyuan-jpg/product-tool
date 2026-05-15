const { chromium } = require('playwright');
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];

  let vp = null;
  for (const p of ctx.pages()) {
    const url = p.url();
    if (url.includes('vercel.com') && url.includes('quickquote')) { vp = p; break; }
  }
  if (!vp) { 
    for (const p of ctx.pages()) {
      if (p.url().includes('vercel.com')) { vp = p; break; }
    }
  }
  if (!vp) { vp = await ctx.newPage(); }

  await vp.goto('https://vercel.com/markyuan-jpgs-projects/quickquote/settings/environment-variables', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(5000);

  // Click "Add Environment Variable" 
  await vp.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      if (b.textContent.trim() === 'Add Environment Variable' && b.tagName === 'BUTTON') {
        b.click(); return;
      }
    }
    // Try any button containing Add Environment
    for (const b of btns) {
      if (b.textContent.trim().includes('Add Environment')) { b.click(); return; }
    }
  });
  await sleep(2000);

  // Check form state
  const formInfo = await vp.evaluate(() => {
    const inputs = document.querySelectorAll('input, textarea, select');
    return Array.from(inputs).map(i => ({
      type: i.type || i.tagName,
      placeholder: i.getAttribute('placeholder') || '',
      name: i.getAttribute('name') || '',
      id: i.id || '',
      value: (i.value || '').substring(0, 30),
    }));
  });
  console.log('Form inputs:', JSON.stringify(formInfo, null, 2));

  // Look for name and value inputs
  const keys = ['NEXT_PUBLIC_API_URL'];
  const vals = ['https://product-tool-production.up.railway.app'];
  
  for (let i = 0; i < keys.length; i++) {
    // Find key input
    const keyInputs = await vp.$$('input[placeholder*="Key"], input[placeholder*="key"], input[placeholder*="Name"], input[placeholder*="name"], input[placeholder*="Variable"]');
    console.log(`Key inputs found: ${keyInputs.length}`);
    
    // Try all visible inputs
    const allInputs = await vp.$$('input:not([type="hidden"])');
    console.log(`All inputs: ${allInputs.length}`);
    for (const inp of allInputs) {
      const ph = await inp.getAttribute('placeholder') || '';
      const ty = await inp.getAttribute('type') || '';
      console.log(`  type=${ty} placeholder="${ph}"`);
    }
  }

  await vp.screenshot({ path: '_vercel_env2.png' });
  console.log('DONE');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
