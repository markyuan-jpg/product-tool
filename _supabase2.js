const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  // Go to project general page to find connection info
  await page.goto('https://supabase.com/dashboard/project/tklljjiwyscncwovampw', {
    timeout: 30000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(3000);
  
  // Get ALL text
  const text = await page.evaluate(() => document.body.innerText);
  console.log('=== Full page text ===');
  console.log(text);
  
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
