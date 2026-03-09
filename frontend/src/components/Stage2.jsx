import { useState, memo, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage2.css';

// Memoized de-anonymization function
function deAnonymizeText(text, labelToModel) {
  if (!labelToModel) return text;
  let result = text;
  Object.entries(labelToModel).forEach(([label, model]) => {
    result = result.replace(new RegExp(label, 'g'), `**${model}**`);
  });
  return result;
}

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

function Stage2({ rankings, labelToModel, aggregateRankings, t }) {
  const [activeTab, setActiveTab] = useState(0);

  // Memoize de-anonymized text to avoid re-computation
  const deAnonymizedRanking = useMemo(
    () => deAnonymizeText(rankings[activeTab]?.ranking, labelToModel),
    [rankings, activeTab, labelToModel]
  );

  if (!rankings || rankings.length === 0) return null;

  return (
    <div className="stage glass stage2">
      <h3 className="stage-title">{t.stage2}</h3>

      <div className="tabs">
        {rankings.map((rank, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? 'active' : ''}`}
            onClick={() => setActiveTab(index)}
          >
            {rank.model}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="ranking-model">{rankings[activeTab].model}</div>
        <div className="ranking-content markdown-content">
          <ReactMarkdown>
            {deAnonymizedRanking}
          </ReactMarkdown>
        </div>

        {rankings[activeTab].parsed_ranking?.length > 0 && (
          <div className="parsed-ranking">
            <div className="list-title">Extracted Ranking:</div>
            <ol>
              {rankings[activeTab].parsed_ranking.map((label, i) => (
                <li key={i}>
                  {labelToModel?.[label] || label}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {aggregateRankings?.length > 0 && (
        <div className="aggregate-rankings">
          <div className="section-title">Street Cred (Aggregate)</div>
          <div className="aggregate-list">
            {aggregateRankings.map((agg, index) => (
              <div key={index} className="aggregate-item glass">
                <span className="rank-position">#{index + 1}</span>
                <span className="rank-model">{agg.model}</span>
                <div className="rank-stats">
                  <span className="rank-score">Avg: {agg.average_rank.toFixed(2)}</span>
                  <span className="rank-count">({agg.rankings_count} votes)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default memo(Stage2);
