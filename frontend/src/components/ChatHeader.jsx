import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';

export default function ChatHeader({ sessionId, onNewSession }) {
  const { t } = useLanguage();

  return (
    <header className="chat-header">
      <div className="header-info">
        <div className="bot-avatar">🌿</div>
        <div>
          <h2>{t('header.title')}</h2>
          <span className="session-tag">
            {t('header.sessionLabel')}{' '}
            {sessionId ? `${sessionId.substring(0, 8)}...` : t('header.sessionStarting')}
          </span>
        </div>
      </div>
      <button
        className="new-session-btn"
        onClick={onNewSession}
        title={t('header.newSessionTitle')}
      >
        ✨ {t('header.newSession')}
      </button>
    </header>
  );
}
