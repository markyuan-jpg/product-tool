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

  // Go directly to the service page
  const serviceUrl = 'https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f/service/1ef412c7-16bf-487c-b8a1-3cd5cd753b69';
  console.log('Navigating to service...');
  await rp.goto(serviceUrl, { timeout: 30000, waitUntil: 'domcontentloaded' });
  await sleep(5000);
  console.log('Service URL:', rp.url());

  const text = await rp.evaluate(() => document.body.innerText);
  console.log('SERVICE PAGE TEXT:', text.substring(0, 4000));

  // Find and click "Variables" tab
  const tabLinks = await rp.evaluate(() => {
    const all = document.querySelectorAll('a, button, [role="tab"]');
    return Array.from(all).map(el => ({
      tag: el.tagName,
      text: el.textContent.trim().substring(0, 30),
      href: el.getAttribute('href') || '',
    }));
  });
  console.log('--- Links ---');
  tabLinks.forEach(l => console.log(`[${l.tag}] "${l.text}" ${l.href}`));

  await rp.screenshot({ path: '_service_page.png' });
  console.log('=== DONE ===');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
