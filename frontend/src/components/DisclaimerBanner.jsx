import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';

export default function DisclaimerBanner() {
  const { t } = useLanguage();

  return (
    <div className="disclaimer-banner" role="alert">
      <div className="disclaimer-content">
        <span className="disclaimer-badge">{t('disclaimer.badge')}</span>
        <p className="disclaimer-text">
          {t('disclaimer.intro')}{' '}
          <strong>{t('disclaimer.emphasis')}</strong>{' '}
          {t('disclaimer.outro')}
        </p>
      </div>
    </div>
  );
}
