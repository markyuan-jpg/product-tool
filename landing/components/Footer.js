'use client';
import { useLocale, t } from '@/lib/i18n';

export default function Footer() {
  const { locale, ready } = useLocale();
  if (!ready) return null;
  return (
    <footer className="border-t border-[var(--border)] py-6 px-6 text-center text-xs text-[var(--text-secondary)]">
      {t('footer.copyright', locale)}
    </footer>
  );
}
