import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './Stage3.css';

// Memoized code renderer
const CodeBlock = memo(function CodeBlock({ inline, className, children, ...props }) {
  const match = /language-(\w+)/.exec(className || '');
  return !inline && match ? (
    <SyntaxHighlighter
      style={oneDark}
      language={match[1]}
      PreTag="div"
      customStyle={{
        margin: 0,
        padding: '16px',
        fontSize: '14px',
        background: 'transparent'
      }}
      {...props}
    >
      {String(children).replace(/\n$/, '')}
    </SyntaxHighlighter>
  ) : (
    <code className={className} style={{ padding: '2px 6px', background: 'var(--bg-tertiary)', borderRadius: '4px' }} {...props}>
      {children}
    </code>
  );
});

function Stage3({ finalResponse, t }) {
  if (!finalResponse) return null;

  return (
    <div className="stage glass stage3">
      <h3 className="stage-title">{t.stage3}</h3>
      <div className="final-response">
        <div className="chairman-label">
          {t.chairman}: {finalResponse.model}
          {finalResponse.actual_model && (
            <span className="actual-model-badge" style={{ marginLeft: '12px' }}>
              {finalResponse.actual_model}
            </span>
          )}
        </div>
        <div className="final-text markdown-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{ code: CodeBlock }}
          >
            {finalResponse.response}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default memo(Stage3);
