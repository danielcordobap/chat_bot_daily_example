import React, { useState } from 'react';
import { useLanguage } from '../i18n/LanguageContext';

export default function MessageInput({ onSendMessage, onStop, isStreaming }) {
  const { t } = useLanguage();
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !isStreaming) {
      onSendMessage(text.trim());
      setText('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <form className="message-input-form" onSubmit={handleSubmit}>
      <textarea
        className="message-textarea"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={t('input.placeholder')}
        rows={1}
      />
      {isStreaming ? (
        <button
          type="button"
          className="stop-button"
          onClick={onStop}
          title={t('input.stopTitle')}
          aria-label={t('input.stopTitle')}
        >
          <span className="stop-icon" aria-hidden="true"></span>
          {t('input.stop')}
        </button>
      ) : (
        <button
          type="submit"
          className="send-button"
          disabled={!text.trim()}
        >
          {t('input.send')}
        </button>
      )}
    </form>
  );
}
