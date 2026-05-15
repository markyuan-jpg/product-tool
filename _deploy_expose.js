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

  // Go to service Settings
  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f/service/1ef412c7-16bf-487c-b8a1-3cd5cd753b69/settings', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(4000);
  console.log('Settings URL:', rp.url());
  
  const text = await rp.evaluate(() => document.body.innerText);
  console.log('Settings page:', text.substring(0, 4000));

  // Look for "Generate Domain" or "Public Networking" section
  const clickables = await rp.evaluate(() => {
    const all = document.querySelectorAll('button, a, [role="button"], label');
    return Array.from(all).map(el => ({
      tag: el.tagName,
      text: el.textContent.replace(/\s+/g, ' ').trim().substring(0, 60),
    }));
  });
  console.log('--- Options ---');
  clickables.filter(c => c.text.length > 0).forEach(c => console.log(`[${c.tag}] "${c.text}"`));

  await rp.screenshot({ path: '_settings.png' });
  console.log('DONE');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
