const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  
  let rp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('railway.com')) { rp = p; break; }
  }
  if (!rp) { console.log('No railway tab'); return; }
  
  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f', { 
    timeout: 20000, waitUntil: 'domcontentloaded' 
  });
  await rp.waitForTimeout(4000);
  
  // Get full page text
  const text = await rp.evaluate(() => document.body.innerText);
  const lines = text.split('\n').filter(l => l.trim());
  
  // Show important sections
  const envLines = lines.filter(l => l.includes('DATABASE') || l.includes('JWT') || l.includes('BASE') || l.includes('RAILWAY') || l.includes('PORT'));
  console.log('=== ENV RELATED ===');
  envLines.forEach(l => console.log(l));
  
  const serviceLines = lines.filter(l => l.includes('product') || l.includes('backend') || l.includes('service') || l.includes('deploy') || l.includes('Deploy') || l.includes('Changes') || l.includes('Variable'));
  console.log('=== SERVICE RELATED ===');
  serviceLines.forEach(l => console.log(l));
  
  // Show raw text around key areas
  console.log('=== FULL TEXT ===');
  console.log(text);
  
  await rp.screenshot({ path: '_railway_full.png' });
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
