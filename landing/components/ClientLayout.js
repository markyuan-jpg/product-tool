'use client';

import ErrorBoundary from './ErrorBoundary';

export default function ClientLayout({ children }) {
  return <ErrorBoundary>{children}</ErrorBoundary>;
}
