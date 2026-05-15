const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  
  let rp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('railway.com')) { rp = p; break; }
  }
  if (!rp) { console.log('No railway tab'); return; }
  
  // Go to project page
  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f', { 
    timeout: 20000, waitUntil: 'domcontentloaded' 
  });
  await rp.waitForTimeout(4000);
  
  console.log('URL:', rp.url());
  const text = await rp.evaluate(() => document.body.innerText.substring(0, 4000));
  console.log(text);
  
  await rp.screenshot({ path: '_railway_project.png' });
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
