const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  await page.goto('https://supabase.com/dashboard/project/tklljjiwyscncwovampw', {
    timeout: 30000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(2000);
  
  // Click "Connect" button
  const connectBtn = await page.evaluate(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
      if (b.textContent.trim() === 'Connect') {
        b.click();
        return 'clicked';
      }
    }
    return 'not found';
  });
  console.log('Connect button:', connectBtn);
  await page.waitForTimeout(1000);
  
  // Now click "Connection string" tab in the modal
  const tabClick = await page.evaluate(() => {
    const btns = document.querySelectorAll('button, [role="tab"], span, div');
    for (const b of btns) {
      const t = b.textContent.trim().toLowerCase();
      if (t === 'connection string' || t === 'connection string ') {
        b.click();
        return 'clicked';
      }
    }
    return 'not found';
  });
  console.log('Tab click:', tabClick);
  await page.waitForTimeout(1000);
  
  // Get connection string from page
  const result = await page.evaluate(() => {
    const text = document.body.innerText;
    const match = text.match(/postgres(?:ql)?:\/\/[^\s"'<>]+/g);
    if (match) return match[0];
    // Also try finding URI params
    const urls = text.match(/db\.[^\s"'<>]+\.supabase\.co/g);
    return urls ? urls[0] : text.substring(0, 3000);
  });
  console.log('RESULT:', result);
  
  await page.screenshot({ path: '_supabase_modal.png' });
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
