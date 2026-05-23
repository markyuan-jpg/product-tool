export default function robots() {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/workspace/', '/login/', '/register/', '/forgot-password/', '/account/', '/api/'],
    },
    sitemap: 'https://quoteflow.it.com/sitemap.xml',
  };
}
