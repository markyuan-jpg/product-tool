const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const defaultContext = browser.contexts()[0];
  const page = await defaultContext.newPage();

  console.log('Navigate to Vercel...');
  await page.goto('https://vercel.com/markyuan-jpgs-projects', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '_vercel_1.png' });
  console.log('Screenshot saved. Check _vercel_1.png');

  // Don't close — that kills user's Edge
  // Just close the new tab
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
