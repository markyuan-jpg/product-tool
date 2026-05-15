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

  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f/service/1ef412c7-16bf-487c-b8a1-3cd5cd753b69/variables', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(4000);

  // Use Raw Editor for speed
  // First try New Variable button
  const btns = await rp.$$('button');
  for (const btn of btns) {
    try {
      const t = ((await btn.textContent()) || '').trim();
      if (t === 'New Variable') {
        console.log('Clicking New Variable');
        await btn.click();
        await sleep(2000);
        break;
      }
    } catch(e) {}
  }

  // Check page after click
  const text = await rp.evaluate(() => document.body.innerText);
  console.log('After click:', text.substring(0, 2000));

  // Try finding input fields
  const inputs = await rp.evaluate(() => {
    const inp = document.querySelectorAll('input, textarea');
    return Array.from(inp).map(i => ({
      type: i.type || i.tagName,
      placeholder: i.getAttribute('placeholder') || '',
      value: i.value?.substring(0, 20) || '',
      id: i.id || '',
      name: i.getAttribute('name') || ''
    }));
  });
  console.log('Inputs:', JSON.stringify(inputs));

  await rp.screenshot({ path: '_add_var.png' });
  console.log('DONE');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
