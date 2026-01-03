import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Settings2 } from 'lucide-react';
import clsx from 'clsx';

const ChatInput = ({ 
  onSend, 
  disabled, 
  model, 
  onModelChange, 
  models = [] 
}) => {
  const [message, setMessage] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-dark-800 bg-dark-900/80 backdrop-blur-xl p-4">
      {/* Model Selector */}
      {showSettings && (
        <div className="mb-3 p-3 bg-dark-800 rounded-lg">
          <label className="block text-sm text-dark-400 mb-2">AI Model</label>
          <select
            value={model}
            onChange={(e) => onModelChange(e.target.value)}
            className="input text-sm"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} - {m.description.slice(0, 50)}...
              </option>
            ))}
          </select>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        <button
          type="button"
          onClick={() => setShowSettings(!showSettings)}
          className={clsx(
            'p-3 rounded-lg transition-colors',
            showSettings ? 'bg-primary-600 text-white' : 'bg-dark-800 text-dark-400 hover:text-dark-200'
          )}
        >
          <Settings2 size={20} />
        </button>

        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={disabled}
            rows={1}
            className="input resize-none pr-12 min-h-[48px] max-h-[200px]"
          />
          <div className="absolute right-2 bottom-2 text-xs text-dark-500">
            {message.length > 0 && `${message.length}/10000`}
          </div>
        </div>

        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className={clsx(
            'p-3 rounded-lg transition-all',
            message.trim() && !disabled
              ? 'bg-primary-600 hover:bg-primary-700 text-white'
              : 'bg-dark-800 text-dark-500 cursor-not-allowed'
          )}
        >
          {disabled ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <Send size={20} />
          )}
        </button>
      </form>

      <p className="text-xs text-dark-500 text-center mt-2">
        ZeroX AI can make mistakes. Consider checking important information.
      </p>
    </div>
  );
};

export default ChatInput;
