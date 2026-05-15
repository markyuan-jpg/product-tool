const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  // Go to Supabase project database settings
  await page.goto('https://supabase.com/dashboard/project/tklljjiwyscncwovampw/settings/database', {
    timeout: 30000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(3000);
  
  console.log('URL:', page.url());
  
  // Get visible text
  const text = await page.evaluate(() => document.body.innerText);
  // Look for connection string
  const lines = text.split('\n').filter(l => l.trim());
  const connStrLines = lines.filter(l => l.includes('postgresql://') || l.includes('postgres://') || l.includes('DATABASE_URL') || l.includes('Connection'));
  console.log('--- Connection related ---');
  connStrLines.forEach(l => console.log(l.substring(0, 200)));
  
  // Look for any postgres connection string
  const pgMatch = text.match(/postgres(?:ql)?:\/\/[^\s"'<>]+/g);
  if (pgMatch) {
    console.log('--- Found connection strings ---');
    pgMatch.forEach(s => console.log(s.substring(0, 150)));
  } else {
    console.log('No connection string found on this page');
    // Show first 2000 chars to debug
    console.log('--- Page text (first 1500) ---');
    console.log(text.substring(0, 1500));
  }
  
  await page.screenshot({ path: '_supabase.png' });
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
