'use client';

import { Component } from 'react';
import { LocaleContext, t } from '@/lib/i18n';

const _capture = (error, errorInfo) => {
  try {
    // Lazy-load Sentry to avoid hard dependency
    import('@sentry/browser').then((Sentry) => {
      Sentry.captureException(error, { extra: { componentStack: errorInfo?.componentStack } });
    }).catch(() => {});
  } catch (_) {}
};

export default class ErrorBoundary extends Component {
  static contextType = LocaleContext;

  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
    _capture(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const locale = this.context?.locale || 'zh';
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          padding: '2rem',
          textAlign: 'center',
          fontFamily: 'system-ui, sans-serif',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 600, margin: '0 0 0.5rem' }}>
            {t('error.title', locale)}
          </h1>
          <p style={{ color: '#666', margin: '0 0 1.5rem', maxWidth: 400 }}>
            {t('error.desc', locale)}
          </p>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            style={{
              padding: '0.5rem 1.5rem',
              background: '#1E3A5F',
              color: '#fff',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
          >
            {t('error.retry', locale)}
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
