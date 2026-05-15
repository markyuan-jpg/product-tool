const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  await page.goto('https://supabase.com/dashboard/project/tklljjiwyscncwovampw', {
    timeout: 30000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(3000);
  
  // Click "Get connected" or "Connection string" button
  const buttons = await page.$$('button, a, div[role="button"]');
  for (const btn of buttons) {
    const text = await btn.textContent();
    if (text && (text.includes('Connection string') || text.includes('Get connected') || text.includes('Connect'))) {
      console.log('Found:', text.trim());
      await btn.click();
      await page.waitForTimeout(1000);
      
      // After clicking, wait and get page text
      const newText = await page.evaluate(() => document.body.innerText);
      const pgMatch = newText.match(/postgres(?:ql)?:\/\/[^\s"'<>]+/g);
      if (pgMatch) {
        console.log('CONNECTION STRING:', pgMatch[0]);
      } else {
        console.log('Text after click:', newText.substring(0, 2000));
      }
      break;
    }
  }
  
  // Also try looking for "Direct" section
  const directBtns = await page.$$('[class*="Direct"], [class*="direct"]');
  console.log('Direct elements found:', directBtns.length);
  
  await page.screenshot({ path: '_supabase_connect.png' });
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
