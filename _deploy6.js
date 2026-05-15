const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  // Go to project Settings → General
  await page.goto('https://vercel.com/markyuan-jpgs-projects/quickquote/settings/general', {
    timeout: 30000, waitUntil: 'networkidle'
  });
  
  // Wait for the page to fully render
  await page.waitForTimeout(5000);
  
  console.log('URL:', page.url());
  console.log('Title:', await page.title());
  
  // Get visible text to understand layout
  const text = await page.evaluate(() => document.body.innerText);
  const lines = text.split('\n').filter(l => l.trim()).map(l => l.trim());
  // Find lines mentioning "Root" or "root" or "Directory"
  const rootLines = lines.filter(l => l.toLowerCase().includes('root') || l.toLowerCase().includes('directory'));
  console.log('--- Root/Directory mentions ---');
  rootLines.forEach(l => console.log(l));
  
  // Find "Root Directory" in full HTML
  const html = await page.content();
  const rootMatch = html.match(/[Rr]oot\s*[Dd]irectory[^<]{0,200}/g);
  if (rootMatch) {
    console.log('--- Root Directory HTML context ---');
    rootMatch.forEach(m => console.log(m.substring(0, 300)));
  }
  
  await page.screenshot({ path: '_vercel_settings.png', fullPage: true });
  console.log('Screenshot saved to _vercel_settings.png');
  
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
