import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import MessageItem from './MessageItem';
import './ChatInterface.css';

export default function ChatInterface({
  conversation,
  onSendMessage,
  onStopSendMessage,
  isLoading,
  t,
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const lastMessageCountRef = useRef(0);
  const resizeTimeoutRef = useRef(null);

  // Scroll only when message count changes (not on every keystroke)
  useEffect(() => {
    const msgCount = conversation?.messages?.length || 0;
    if (msgCount !== lastMessageCountRef.current) {
      lastMessageCountRef.current = msgCount;
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation?.messages?.length]);

  // Debounced textarea resize - prevents lag on every keystroke
  const resizeTextarea = useCallback(() => {
    if (resizeTimeoutRef.current) {
      clearTimeout(resizeTimeoutRef.current);
    }
    resizeTimeoutRef.current = setTimeout(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
      }
    }, 50); // 50ms debounce
  }, []);

  useEffect(() => {
    resizeTextarea();
    return () => {
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
    };
  }, [input, resizeTextarea]);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (isLoading) {
      onStopSendMessage();
      return;
    }

    if (input.trim()) {
      onSendMessage(input);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state glass">
          <h2>{t.new_chat}</h2>
          <p>{t.type_message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <div className="messages-container scrollable">
        {conversation.messages.length === 0 ? (
          <div className="empty-state glass">
            <h2>{t.new_chat}</h2>
            <p>{t.type_message}</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <MessageItem key={index} msg={msg} index={index} t={t} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area glass">
        <form className="input-form" onSubmit={handleSubmit}>
          <textarea
            ref={textareaRef}
            className="message-input"
            placeholder={t.type_message}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
          />
          <button
            type="submit"
            className={`send-button ${isLoading ? 'stop' : ''}`}
            disabled={!input.trim() && !isLoading}
          >
            {isLoading ? t.stop : t.send}
          </button>
        </form>
      </div>
    </div>
  );
}
