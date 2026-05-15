const { chromium } = require('playwright');
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  let rp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('railway.com')) { rp = p; break; }
  }
  if (!rp) { console.log('No railway tab'); return; }

  // Go to service deployments
  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f/service/1ef412c7-16bf-487c-b8a1-3cd5cd753b69', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(4000);

  const text = await rp.evaluate(() => document.body.innerText);
  // Look for error/fail messages
  const lines = text.split('\n').filter(l => l.trim());
  const failLines = lines.filter(l => l.toLowerCase().includes('fail') || l.toLowerCase().includes('error') || l.toLowerCase().includes('build') || l.toLowerCase().includes('log'));
  console.log('Fail/Error related:', failLines.slice(0, 20));
  
  // Try clicking on the latest deployment to see logs
  await rp.evaluate(() => {
    const links = document.querySelectorAll('a');
    for (const a of links) {
      const text = a.textContent.trim().toLowerCase();
      if (text.includes('fail') || text.includes('error') || text.includes('build') && a.getAttribute('href')?.includes('deploy')) {
        a.click(); return;
      }
    }
  });
  await sleep(3000);
  
  const logText = await rp.evaluate(() => document.body.innerText);
  console.log('Deploy log (first 3000):', logText.substring(0, 3000));
  
  await rp.screenshot({ path: '_build_fail.png' });
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
