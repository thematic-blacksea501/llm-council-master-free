import { useState, memo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './Stage1.css';

// Memoized code renderer component
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
    <code className={className} style={{ padding: '2px 4px', background: 'var(--bg-tertiary)', borderRadius: '4px' }} {...props}>
      {children}
    </code>
  );
});

// Memoized tab button
const TabButton = memo(function TabButton({ isActive, onClick, children }) {
  return (
    <button
      className={`tab ${isActive ? 'active' : ''}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
});

function Stage1({ responses, t }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!responses || responses.length === 0) return null;

  return (
    <div className="stage glass stage1">
      <h3 className="stage-title">{t.stage1}</h3>

      <div className="tabs">
        {responses.map((resp, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? 'active' : ''}`}
            onClick={() => setActiveTab(index)}
          >
            {resp.model}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="model-name">
          {responses[activeTab].model} 
          {responses[activeTab].actual_model && (
            <span className="actual-model-badge">
              {responses[activeTab].actual_model}
            </span>
          )}
        </div>
        <div className="response-text markdown-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{ code: CodeBlock }}
          >
            {responses[activeTab].response}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default memo(Stage1);
