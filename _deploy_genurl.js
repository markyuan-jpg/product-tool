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

  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f/service/1ef412c7-16bf-487c-b8a1-3cd5cd753b69/settings', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(4000);

  // Click "Generate Domain" 
  await rp.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      if (b.textContent.trim() === 'Generate Domain') { b.click(); return; }
    }
  });
  await sleep(5000);
  
  const text = await rp.evaluate(() => document.body.innerText);
  console.log('After Generate Domain:', text.substring(0, 3000));
  
  // Look for generated domain
  const domainLines = text.split('\n').filter(l => l.includes('.railway') || l.includes('.up.railway') || l.includes('Domain') || l.includes('domain'));
  console.log('=== Domain lines ===');
  domainLines.forEach(l => console.log(l));
  
  await rp.screenshot({ path: '_domain.png' });
  console.log('DONE');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
