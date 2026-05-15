const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  // Go to project Settings → General
  await page.goto('https://vercel.com/markyuan-jpgs-projects/quickquote/settings/general', {
    timeout: 20000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(3000);
  
  console.log('URL:', page.url());
  console.log('Title:', await page.title());
  
  // Find Root Directory field
  const html = await page.content();
  
  // Search for root directory input
  const rootDir = await page.$('input[value="landing"], input[name="rootDirectory"], input[placeholder*="root"], input[placeholder*="Root"]');
  if (rootDir) {
    const val = await rootDir.inputValue();
    console.log('Root Directory current value:', val);
    // Clear and set new value
    await rootDir.click({ clickCount: 3 });
    await rootDir.fill('');
    await page.waitForTimeout(500);
    console.log('Root Directory cleared');
  } else {
    console.log('Root Directory input not found');
    // Try finding any text input
    const inputs = await page.$$('input[type="text"]');
    for (const inp of inputs) {
      const placeholder = await inp.getAttribute('placeholder') || '';
      const name = await inp.getAttribute('name') || '';
      const id = await inp.getAttribute('id') || '';
      console.log(`Input: placeholder="${placeholder}" name="${name}" id="${id}"`);
    }
    // Try finding "Root Directory" label
    const labels = await page.$$('label');
    for (const label of labels) {
      const text = await label.textContent();
      if (text && text.toLowerCase().includes('root')) {
        console.log('Found label:', text);
        const forAttr = await label.getAttribute('for');
        console.log('Label for:', forAttr);
      }
    }
    // Just dump sections
    const sections = await page.$$('section, div[class*="Section"], div[class*="section"]');
    console.log(`Found ${sections.length} sections`);
  }
  
  await page.screenshot({ path: '_vercel_settings.png', fullPage: true });
  console.log('Screenshot saved');
  
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
