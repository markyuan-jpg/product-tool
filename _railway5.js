const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  
  let rp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('railway.com')) { rp = p; break; }
  }
  if (!rp) { console.log('No railway tab'); return; }
  
  await rp.goto('https://railway.com/dashboard', { timeout: 20000, waitUntil: 'domcontentloaded' });
  await rp.waitForTimeout(2000);
  
  // Get all links and their hrefs
  const linkInfo = await rp.evaluate(() => {
    const links = document.querySelectorAll('a');
    return Array.from(links).map(l => ({
      text: l.textContent.trim().substring(0, 50),
      href: l.getAttribute('href')
    })).filter(l => l.text && l.text.length > 0);
  });
  
  // Find stellar links
  const stellarLinks = linkInfo.filter(l => l.text.includes('stellar') || l.href?.includes('stellar'));
  console.log('Stellar links:');
  stellarLinks.forEach(l => console.log(`  text="${l.text}" href="${l.href}"`));
  
  // Also print first 20 links for debugging
  console.log('All links (first 15):');
  linkInfo.slice(0, 15).forEach(l => console.log(`  "${l.text}" -> ${l.href}`));
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
