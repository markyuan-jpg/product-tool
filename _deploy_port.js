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
  await sleep(5000);

  // Click Generate Domain button
  await rp.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      if (b.textContent.trim() === 'Generate Domain' && b.getAttribute('type') !== 'button') {
        b.click(); 
        return 'clicked';
      }
    }
    // Try the first one
    for (const b of btns) {
      if (b.textContent.trim() === 'Generate Domain') {
        b.click(); 
        return 'clicked-first';
      }
    }
    return 'not-found';
  });
  await sleep(3000);

  // Find the port input (type=number, placeholder=8080)
  const portInput = await rp.$('input[type="number"]');
  if (portInput) {
    await portInput.click();
    await portInput.fill('');
    await sleep(300);
    await portInput.fill('8080');
    console.log('Port filled');
    await sleep(500);
  }

  // Now find ALL "Generate Domain" buttons
  const allBtns = await rp.$$('button');
  console.log(`Found ${allBtns.length} buttons`);
  for (const btn of allBtns) {
    const t = ((await btn.textContent()) || '').trim();
    const disabled = await btn.getAttribute('disabled');
    const type = await btn.getAttribute('type');
    if (t === 'Generate Domain') {
      console.log(`Generate Domain btn: disabled=${disabled} type=${type}`);
    }
  }

  // Try clicking each Generate Domain button
  for (const btn of allBtns) {
    const t = ((await btn.textContent()) || '').trim();
    if (t === 'Generate Domain') {
      const isDisabled = await btn.getAttribute('disabled');
      if (!isDisabled) {
        await btn.click();
        await sleep(5000);
        console.log('Clicked!');
        break;
      }
    }
  }

  const text = await rp.evaluate(() => document.body.innerText);
  const domain = text.match(/https?:\/\/[^\s"'<>]*\.up\.railway[^\s"'<>]*/g);
  if (domain) {
    console.log('DOMAIN:', domain[0]);
  } else if (text.includes('Generate Service Domain')) {
    console.log('Dialog still open');
  } else {
    // Check for new URL
    const urls = text.match(/https?:\/\/[^\s"'<>]*railway[^\s"'<>]*/g);
    console.log('URLs found:', urls);
    console.log('Text:', text.substring(0, 2000));
  }

  await rp.screenshot({ path: '_port_done.png' });
  console.log('DONE');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
