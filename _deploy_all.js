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

  console.log('=== Railway Project Page ===');
  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(5000);
  console.log('URL:', rp.url());

  // Scroll to find services area
  await rp.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await sleep(1000);

  // Find all clickable things
  const clicks = await rp.evaluate(() => {
    const all = document.querySelectorAll('a, button, [role="button"], [tabindex="0"]');
    return Array.from(all).slice(0, 50).map(el => ({
      tag: el.tagName,
      text: el.textContent.trim().substring(0, 40),
      href: el.getAttribute('href') || '',
      class: el.className?.substring(0, 40) || ''
    }));
  });
  console.log('=== Clickable elements (first 30) ===');
  clicks.slice(0, 30).forEach(c => console.log(`[${c.tag}] "${c.text}" href=${c.href}`));

  // Try going to service directly if we can find the URL pattern
  // Look for any service link
  const serviceMatch = clicks.find(c => c.text === 'product-tool');
  if (serviceMatch) {
    console.log('Found product-tool element');
    // Try clicking
    const el = await rp.$(`a:has-text("product-tool"), button:has-text("product-tool")`);
    if (el) {
      await el.click();
      await sleep(5000);
      console.log('After click URL:', rp.url());
    }
  }

  const text = await rp.evaluate(() => document.body.innerText);
  console.log('=== Current page text ===');
  console.log(text.substring(0, 4000));
  
  await rp.screenshot({ path: '_deploy_state.png' });
  console.log('=== SCREENSHOT SAVED ===');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
