'use client';
import { useLocale, t } from '@/lib/i18n';

export default function Footer() {
  const { locale, ready } = useLocale();
  if (!ready) return null;
  return (
    <footer className="border-t border-[var(--border)] py-6 px-6 text-center text-xs text-[var(--text-secondary)] space-y-2">
      <p>{t('footer.copyright', locale)}</p>
      <p className="space-x-4">
        <a href="/terms" className="hover:text-[var(--navy)] underline underline-offset-2">{t('footer.terms', locale)}</a>
        <a href="/privacy" className="hover:text-[var(--navy)] underline underline-offset-2">{t('footer.privacy', locale)}</a>
      </p>
    </footer>
  );
}
