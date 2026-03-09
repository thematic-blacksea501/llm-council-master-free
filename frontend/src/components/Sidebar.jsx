import { useEffect, useState } from 'react';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRenameConversation,
  settings,
  setSettings,
  t,
}) {
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [chainsJson, setChainsJson] = useState(JSON.stringify(settings.chains, null, 2));

  useEffect(() => {
    setChainsJson(JSON.stringify(settings.chains, null, 2));
  }, [settings.chains]);

  const handleSaveChains = () => {
    try {
      const parsed = JSON.parse(chainsJson);
      setSettings({ ...settings, chains: parsed });
      alert(t.settings_saved);
    } catch {
      alert(t.invalid_json);
    }
  };

  const startEditing = (e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title || '');
  };

  const submitRename = (e) => {
    e.preventDefault();
    if (editTitle.trim() && editTitle !== conversations.find((c) => c.id === editingId)?.title) {
      onRenameConversation(editingId, editTitle);
    }
    setEditingId(null);
  };

  const cancelEditing = () => {
    setEditingId(null);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          {t.new_chat}
        </button>
      </div>

      <div className="conversation-list scrollable">
        <div className="section-title">{t.conversations}</div>
        {conversations.length === 0 ? (
          <div className="no-conversations">...</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              } ${editingId === conv.id ? 'editing' : ''}`}
              onClick={() => onSelectConversation(conv.id)}
              onDoubleClick={(e) => startEditing(e, conv)}
            >
              <div className="conversation-title">
                {editingId === conv.id ? (
                  <form onSubmit={submitRename} onClick={(e) => e.stopPropagation()}>
                    <input
                      autoFocus
                      className="edit-title-input"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onBlur={submitRename}
                      onKeyDown={(e) => e.key === 'Escape' && cancelEditing()}
                    />
                  </form>
                ) : (
                  conv.title || t.new_chat
                )}
              </div>
              <div className="conversation-actions">
                <button
                  className="action-btn rename-btn"
                  onClick={(e) => startEditing(e, conv)}
                  title={t.rename_chat}
                >
                  Edit
                </button>
                <button
                  className="action-btn delete-btn"
                  onClick={(e) => onDeleteConversation(e, conv.id)}
                  title={t.delete_chat}
                >
                  Del
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer settings-section">
        <div className="section-title">{t.settings}</div>

        <div className="setting-item">
          <span>{t.theme}</span>
          <div className="toggle-group">
            <button
              className={settings.theme === 'dark' ? 'active' : ''}
              onClick={() => setSettings({ ...settings, theme: 'dark' })}
            >
              {t.dark}
            </button>
            <button
              className={settings.theme === 'light' ? 'active' : ''}
              onClick={() => setSettings({ ...settings, theme: 'light' })}
            >
              {t.light}
            </button>
          </div>
        </div>

        <div className="setting-item">
          <span>{t.language}</span>
          <div className="toggle-group">
            <button
              className={settings.lang === 'ru' ? 'active' : ''}
              onClick={() => setSettings({ ...settings, lang: 'ru' })}
            >
              RU
            </button>
            <button
              className={settings.lang === 'en' ? 'active' : ''}
              onClick={() => setSettings({ ...settings, lang: 'en' })}
            >
              EN
            </button>
          </div>
        </div>

        <div className="setting-item-col">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={settings.forceRussian}
              onChange={(e) => setSettings({ ...settings, forceRussian: e.target.checked })}
            />
            <span>{t.force_russian}</span>
          </label>
        </div>

        <div className="advanced-toggle" onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}>
          {t.advanced_settings} {isAdvancedOpen ? 'v' : '>'}
        </div>

        {isAdvancedOpen && (
          <div className="advanced-settings-panel">
            <div className="setting-item-col">
              <label>{t.chairman_selection}</label>
              <select
                value={settings.chairman}
                onChange={(e) => setSettings({ ...settings, chairman: e.target.value })}
              >
                {Object.keys(settings.chains).map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            <div className="setting-item-col">
              <label>
                {t.creativity} ({settings.temperature})
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
              />
            </div>

            <div className="setting-item-col">
              <label>{t.system_prompt}</label>
              <textarea
                className="chains-editor"
                style={{ height: '80px' }}
                value={settings.systemPrompt}
                onChange={(e) => setSettings({ ...settings, systemPrompt: e.target.value })}
                placeholder="Custom instruction..."
                spellCheck="false"
              />
            </div>

            <div className="setting-item-col" style={{ marginBottom: '16px' }}>
              <label className="checkbox-label" style={{ textTransform: 'none', letterSpacing: 'normal' }}>
                <input
                  type="checkbox"
                  checked={settings.autoDetectLang !== false}
                  onChange={(e) => setSettings({ ...settings, autoDetectLang: e.target.checked })}
                />
                <span>{t.auto_detect_lang}</span>
              </label>
            </div>

            <div className="setting-item-col">
              <label>{t.council_chains}</label>
              <textarea
                className="chains-editor"
                value={chainsJson}
                onChange={(e) => setChainsJson(e.target.value)}
                spellCheck="false"
              />
              <button className="save-chains-btn" onClick={handleSaveChains}>
                {t.save_settings}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
