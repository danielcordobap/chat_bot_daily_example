const API_BASE_URL = 'http://localhost:8000/api';

export async function createThread() {
  try {
    const response = await fetch(`${API_BASE_URL}/threads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) {
      throw { code: 'THREAD_CREATE_FAILED', status: response.status };
    }
    return await response.json();
  } catch (err) {
    if (err && err.code) {
      throw err;
    }
    throw { code: 'THREAD_CREATE_FAILED' };
  }
}

export function streamChatMessage(sessionId, message, onChunk, onError, onComplete) {
  const controller = new AbortController();

  fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify({ session_id: sessionId, message: message }),
    signal: controller.signal
  })
    .then(async (response) => {
      if (!response.ok) {
        throw { code: 'SERVER_ERROR', status: response.status };
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (dataStr === '[DONE]') {
              onComplete();
              return;
            }
            try {
              const data = JSON.parse(dataStr);
              if (data.error) {
                onError({ code: 'UNKNOWN', detail: data.error });
                return;
              }
              onChunk(data);
            } catch (err) {
              console.error('Error parsing SSE event:', err);
            }
          }
        }
      }
      onComplete();
    })
    .catch((err) => {
      if (err.name === 'AbortError') return;
      if (err && err.code) {
        onError(err);
      } else {
        onError({ code: 'NETWORK_ERROR' });
      }
    });

  return () => controller.abort();
}
