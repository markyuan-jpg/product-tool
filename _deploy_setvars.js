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

  const varsUrl = 'https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f/service/1ef412c7-16bf-487c-b8a1-3cd5cd753b69/variables';
  await rp.goto(varsUrl, { timeout: 30000, waitUntil: 'domcontentloaded' });
  await sleep(4000);

  const varsToAdd = [
    { name: 'JWT_SECRET_KEY', value: 'd2f8a1e3c9b74d5f8a2e6c3b9d1f4a7e' },
    { name: 'DATABASE_URL', value: 'postgresql+asyncpg://postgres:Yb857151464%21@db.tklljjiwyscncwovampw.supabase.co:5432/postgres' },
    { name: 'BASE_URL', value: 'https://quickquote-murex.vercel.app' },
  ];

  for (const v of varsToAdd) {
    console.log(`Adding ${v.name}...`);
    
    // Click New Variable
    await rp.evaluate(() => {
      const btns = document.querySelectorAll('button');
      for (const b of btns) {
        if (b.textContent.trim() === 'New Variable') { b.click(); return; }
      }
    });
    await sleep(1000);
    
    // Fill name field
    await rp.fill('textarea[placeholder="VARIABLE_NAME"]', v.name);
    await sleep(300);
    
    // Fill value field (placeholder has special chars so use partial match)
    await rp.fill('textarea[placeholder^="VALUE"]', v.value);
    await sleep(300);
    
    // Click Add
    await rp.evaluate(() => {
      const btns = document.querySelectorAll('button');
      for (const b of btns) {
        if (b.textContent.trim() === 'Add') { b.click(); return; }
      }
    });
    await sleep(2000);
    console.log(`  Added ${v.name}`);
    
    await rp.screenshot({ path: `_var_${v.name}.png` });
  }
  
  console.log('=== ALL VARIABLES ADDED ===');
  const text = await rp.evaluate(() => document.body.innerText);
  const varLines = text.split('\n').filter(l => l.includes('JWT') || l.includes('DATABASE') || l.includes('BASE_URL') || l.includes('PORT'));
  console.log('Current variables:', varLines);
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
