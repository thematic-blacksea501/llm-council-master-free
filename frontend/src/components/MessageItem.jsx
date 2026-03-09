import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import './ChatInterface.css';

// Memoized message item - only re-renders when its own data changes
const MessageItem = memo(function MessageItem({ msg, index, t }) {
  return (
    <div className={`message-group ${msg.role}`}>
      <div className="message-header">
        <span className="message-label">
          {msg.role === 'user' ? t.you : t.council_name}
        </span>
      </div>

      <div className="message-body">
        {msg.role === 'user' ? (
          <div className="user-text glass">
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
            </div>
            {msg.metadata?.force_russian && (
              <div className="message-meta">
                <details>
                  <summary>{t.system_instructions}</summary>
                  <div className="meta-prompt">
                    {msg.metadata?.system_prompt || t.force_russian_hint}
                  </div>
                </details>
              </div>
            )}
          </div>
        ) : (
          <div className="assistant-stages">
            {msg.loading?.stage1 && (
              <div className="stage-loading glass">
                <div className="loader"></div>
                <span>
                  {t.stage1} {t.thinking}
                </span>
              </div>
            )}
            {msg.stage1 && <Stage1 responses={msg.stage1} t={t} />}

            {msg.loading?.stage2 && (
              <div className="stage-loading glass">
                <div className="loader"></div>
                <span>
                  {t.stage2} {t.thinking}
                </span>
              </div>
            )}
            {msg.stage2 && (
              <Stage2
                rankings={msg.stage2}
                labelToModel={msg.metadata?.label_to_model}
                aggregateRankings={msg.metadata?.aggregate_rankings}
                t={t}
              />
            )}

            {msg.loading?.stage3 && (
              <div className="stage-loading glass">
                <div className="loader"></div>
                <span>
                  {t.stage3} {t.thinking}
                </span>
              </div>
            )}
            {msg.stage3 && <Stage3 finalResponse={msg.stage3} t={t} />}

            {msg.error && (
              <div className="stage-error glass">
                <span className="error-icon">!</span>
                <div className="error-content">
                  <div className="error-title">{t.error_title}</div>
                  <div className="error-message">{msg.error}</div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison - only re-render if message data actually changed
  const prevMsg = prevProps.msg;
  const nextMsg = nextProps.msg;
  
  return (
    prevMsg.content === nextMsg.content &&
    prevMsg.stage1 === nextMsg.stage1 &&
    prevMsg.stage2 === nextMsg.stage2 &&
    prevMsg.stage3 === nextMsg.stage3 &&
    prevMsg.error === nextMsg.error &&
    prevMsg.loading?.stage1 === nextMsg.loading?.stage1 &&
    prevMsg.loading?.stage2 === nextMsg.loading?.stage2 &&
    prevMsg.loading?.stage3 === nextMsg.loading?.stage3 &&
    prevMsg.metadata === nextMsg.metadata
  );
});

export default MessageItem;
