const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  await page.goto('https://supabase.com/dashboard/project/tklljjiwyscncwovampw', {
    timeout: 30000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(2000);
  
  // Click Connect
  const els = await page.$$('button, [role="button"], [role="tab"], span, div, a');
  for (const el of els) {
    const t = ((await el.textContent()) || '').trim();
    if (t === 'Connect' && (await el.tagName()) === 'BUTTON') {
      await el.click();
      console.log('Clicked Connect');
      break;
    }
  }
  await page.waitForTimeout(1000);
  
  // Now look for "Connection string" in ANY clickable element in the dialog
  const tabs = await page.$$('[role="tab"], [role="button"], button, span, div');
  for (const tab of tabs) {
    const t = ((await tab.textContent()) || '').trim();
    if (t === 'Connection string' || t === 'Direct') {
      console.log('Clicking tab:', t);
      await tab.click();
      await page.waitForTimeout(1000);
      
      const text = await page.evaluate(() => document.body.innerText);
      // Look for connection string
      const pgMatch = text.match(/postgres(?:ql)?:\/\/[^\s"'<>]+/g);
      if (pgMatch) {
        console.log('CONNECTION STRING:', pgMatch[0]);
      } else {
        // Look for password field
        const passwordMatch = text.match(/[Pp]assword[^a-z][^\n]{0,100}/g);
        if (passwordMatch) console.log('Password:', passwordMatch[0]);
        // Show section content
        const lines = text.split('\n').filter(l => l.trim());
        const sectionLines = lines.filter(l => l.includes('postgres') || l.includes('5432') || l.includes('password') || l.includes('Password'));
        sectionLines.forEach(l => console.log(l.trim()));
      }
      break;
    }
  }
  
  await page.screenshot({ path: '_supabase_conn.png' });
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
