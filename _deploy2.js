const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const defaultContext = browser.contexts()[0];
  const page1 = defaultContext.pages()[0];
  
  console.log('Current page URL:', page1.url());
  console.log('Current page title:', await page1.title());
  
  // Check if logged into Vercel by navigating
  const page = await defaultContext.newPage();
  try {
    await page.goto('https://vercel.com', { timeout: 15000, waitUntil: 'domcontentloaded' });
    console.log('Title:', await page.title());
    console.log('URL:', page.url());
    
    // Check if login page or dashboard
    const html = await page.content();
    if (html.includes('login') || html.includes('Log in') || html.includes('Sign In')) {
      console.log('STATUS: NOT_LOGGED_IN');
    } else if (html.includes('dashboard') || html.includes('Dashboard') || html.includes('markyuan')) {
      console.log('STATUS: LOGGED_IN');
    } else {
      console.log('STATUS: UNKNOWN');
    }
  } catch (e) {
    console.log('Navigation error:', e.message);
  }
  
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
