export default function robots() {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/workspace/', '/login/', '/register/', '/forgot-password/', '/account/', '/api/'],
    },
    sitemap: 'https://quotation-tool.vercel.app/sitemap.xml',
  };
}
