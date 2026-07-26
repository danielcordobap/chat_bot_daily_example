import React, { useState, useEffect, useRef } from 'react';
import DisclaimerBanner from './components/DisclaimerBanner';
import ChatHeader from './components/ChatHeader';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import LanguageToggle from './components/LanguageToggle';
import { createThread, streamChatMessage } from './services/api';
import { useLanguage } from './i18n/LanguageContext';

export default function App() {
  const { t } = useLanguage();
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [errorObj, setErrorObj] = useState(null);
  const abortRef = useRef(null);

  const initSession = async () => {
    try {
      setErrorObj(null);
      const data = await createThread();
      setSessionId(data.session_id);
      setMessages([]);
    } catch (err) {
      console.error('Error initializing thread:', err);
      setErrorObj(err && err.code ? err : { code: 'threadCreate' });
      setSessionId(crypto.randomUUID());
    }
  };

  useEffect(() => {
    initSession();
  }, []);

  const handleSendMessage = (text) => {
    setErrorObj(null);
    const userMsg = { sender: 'user', text: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setIsStreaming(true);

    let assistantMsgIndex = null;

    abortRef.current = streamChatMessage(
      sessionId,
      text,
      (data) => {
        setIsLoading(false);
        setMessages((prev) => {
          const newMsgs = [...prev];
          if (assistantMsgIndex === null) {
            assistantMsgIndex = newMsgs.length;
            newMsgs.push({
              sender: 'assistant',
              text: data.content,
              is_crisis: data.is_crisis,
              quote: data.quote
            });
          } else {
            newMsgs[assistantMsgIndex] = {
              ...newMsgs[assistantMsgIndex],
              text: data.content,
              is_crisis: data.is_crisis,
              quote: data.quote
            };
          }
          return newMsgs;
        });
      },
      (error) => {
        setIsLoading(false);
        setIsStreaming(false);
        abortRef.current = null;
        setErrorObj(typeof error === 'object' ? error : { code: 'unknown' });
      },
      () => {
        setIsLoading(false);
        setIsStreaming(false);
        abortRef.current = null;
      }
    );
  };

  const handleStopGeneration = () => {
    // DEMO: Detener aborta la petición del navegador, pero el backend sigue generando hasta
    // terminar. Cancelar de verdad la llamada al modelo exige propagar la desconexión del
    // cliente hasta el nodo del grafo.
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
    setIsLoading(false);
    setIsStreaming(false);
  };

  const getErrorMessage = () => {
    if (!errorObj) return '';
    const code = errorObj.code;
    if (code === 'THREAD_CREATE_FAILED') return t('errors.threadCreate');
    if (code === 'SERVER_ERROR') return t('errors.server', { status: errorObj.status || 500 });
    if (code === 'NETWORK_ERROR') return t('errors.network');
    if (code === 'UNKNOWN') return t('errors.unknown');
    return t(`errors.${code}`, errorObj) || t('errors.unknown');
  };

  return (
    <div className="app-container">
      {/* CAM-05: DisclaimerBanner fijo fuera de la zona de scroll */}
      <DisclaimerBanner />

      <div className="layout-body">
        <LanguageToggle />
        <div className="main-chat-card">
          <ChatHeader sessionId={sessionId} onNewSession={initSession} />

          {errorObj && (
            <div className="error-banner">
              <span>⚠️ {getErrorMessage()}</span>
            </div>
          )}

          <ChatWindow messages={messages} isLoading={isLoading} />
          <MessageInput
            onSendMessage={handleSendMessage}
            onStop={handleStopGeneration}
            isStreaming={isStreaming}
          />
        </div>
      </div>
    </div>
  );
}
