const { chromium } = require('playwright');
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];

  // ─── Step 1: Trigger Railway Deploy ───
  let rp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('railway.com')) { rp = p; break; }
  }
  
  if (rp) {
    console.log('=== Triggering Railway Deploy ===');
    // Go to service deployments
    await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f/service/1ef412c7-16bf-487c-b8a1-3cd5cd753b69', { 
      timeout: 30000, waitUntil: 'domcontentloaded' 
    });
    await sleep(3000);
    
    // Click Deploy button
    await rp.evaluate(() => {
      const btns = document.querySelectorAll('button');
      for (const b of btns) {
        if (b.textContent.trim().includes('Deploy')) { b.click(); return; }
      }
    });
    await sleep(3000);
    console.log('Deploy triggered');
  }

  // ─── Step 2: Set Vercel env var ───
  let vp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('vercel.com')) { vp = p; break; }
  }
  
  if (vp) {
    console.log('=== Setting Vercel ENV ===');
    // Navigate to environment variables
    await vp.goto('https://vercel.com/markyuan-jpgs-projects/quickquote/settings/environment-variables', { 
      timeout: 30000, waitUntil: 'domcontentloaded' 
    });
    await sleep(5000);
    
    // Look for "Add Environment Variable" or similar button
    const addInfo = await vp.evaluate(() => {
      const btns = document.querySelectorAll('button, a, [role="button"]');
      return Array.from(btns).map(b => ({
        text: b.textContent.replace(/\s+/g, ' ').trim().substring(0, 50),
        tag: b.tagName
      }));
    });
    console.log('Buttons:', addInfo.filter(b => b.text.includes('Add') || b.text.includes('Environment') || b.text.includes('Variable')).map(b => b.text));
    
    const text = await vp.evaluate(() => document.body.innerText);
    const envLines = text.split('\n').filter(l => l.includes('API') || l.includes('NEXT_PUBLIC') || l.includes('Environment') || l.includes('Add'));
    console.log('ENV page:', envLines.slice(0, 20));
    
    await vp.screenshot({ path: '_vercel_env.png' });
  }
  
  console.log('=== DONE ===');
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
