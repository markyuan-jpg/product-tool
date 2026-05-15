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
  await sleep(2000);

  // Fill port number
  const portInput = await rp.$('input[type="text"], input[type="number"]');
  if (portInput) {
    await portInput.fill('8080');
    console.log('Filled port: 8080');
    await sleep(500);
  }

  // Look for Generate/Generate Domain button in dialog
  await rp.evaluate(() => {
    const btns = document.querySelectorAll('button');
    // Get last Generate Domain button which should be in the dialog
    const genBtns = [];
    for (const b of btns) {
      if (b.textContent.trim() === 'Generate Domain' || b.textContent.trim() === 'Generate') {
        genBtns.push(b);
      }
    }
    // Click the last one (dialog button)
    if (genBtns.length > 0) genBtns[genBtns.length - 1].click();
  });
  await sleep(3000);

  const text = await rp.evaluate(() => document.body.innerText);
  const domainLines = text.split('\n').filter(l => l.includes('.railway') || l.includes('.up.railway') || l.includes('https://'));
  console.log('Domain lines:', domainLines);
  console.log('Page text after:', text.substring(0, 2000));

  await rp.screenshot({ path: '_domain2.png' });
  console.log('DONE');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
