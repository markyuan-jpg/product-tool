'use client';

import { useEffect } from 'react';

export default function SentryInit() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (!dsn) return;
    import('@sentry/browser').then((Sentry) => {
      Sentry.init({ dsn, environment: process.env.NODE_ENV || 'production' });
    }).catch(() => {});
  }, []);
  return null;
}
