import React, { useEffect, useRef } from 'react';
import CrisisCard from './CrisisCard';
import { useLanguage } from '../i18n/LanguageContext';

export default function ChatWindow({ messages, isLoading }) {
  const { t } = useLanguage();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">💬</div>
          <h3>{t('empty.title')}</h3>
          <p>{t('empty.body')}</p>
        </div>
      ) : (
        messages.map((msg, index) => (
          <div key={index} className={`message-bubble-wrapper ${msg.sender}`}>
            <div className={`message-bubble ${msg.sender} ${msg.is_crisis ? 'crisis' : ''}`}>
              <div className="message-content">{msg.text}</div>

              {/* Si se incluyó una cita célebre real y verificada */}
              {msg.quote && (
                <div className="quote-card">
                  <div className="quote-icon">“</div>
                  <blockquote className="quote-text">{msg.quote.text}</blockquote>
                  <div className="quote-attribution">
                    — <strong>{msg.quote.author}</strong>, <em>{msg.quote.source}</em>
                  </div>
                </div>
              )}

              {/* Si se activó la rama de crisis (CAM-05) */}
              {msg.is_crisis && (
                <CrisisCard
                  message={msg.text}
                  resources={msg.crisis_resources || []}
                />
              )}
            </div>
          </div>
        ))
      )}

      {isLoading && (
        <div className="message-bubble-wrapper assistant">
          <div className="message-bubble assistant loading">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
