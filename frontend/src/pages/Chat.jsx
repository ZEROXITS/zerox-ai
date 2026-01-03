import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import { useAuth } from '../context/AuthContext';
import { chatAPI, modelsAPI, streamChat } from '../utils/api';

const Chat = () => {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('llama-3.1-70b-versatile');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [authLoading, isAuthenticated, navigate]);

  useEffect(() => {
    if (isAuthenticated) {
      loadConversations();
      loadModels();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = async () => {
    try {
      const response = await chatAPI.getConversations();
      setConversations(response.data);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const loadModels = async () => {
    try {
      const response = await modelsAPI.getModels();
      setModels(response.data.models);
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  };

  const loadConversation = async (conv) => {
    setCurrentConversation(conv);
    setSelectedModel(conv.model);
    
    try {
      const response = await chatAPI.getConversation(conv.id);
      setMessages(response.data.messages);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleNewChat = () => {
    setCurrentConversation(null);
    setMessages([]);
  };

  const handleDeleteConversation = (id) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentConversation?.id === id) {
      handleNewChat();
    }
  };

  const handleSendMessage = useCallback(async (content) => {
    if (isLoading || isStreaming) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIsStreaming(true);

    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      model_used: selectedModel,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, assistantMessage]);

    await streamChat(
      {
        message: content,
        conversation_id: currentConversation?.id,
        model: selectedModel,
      },
      // onChunk
      (chunk) => {
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg.role === 'assistant') {
            lastMsg.content += chunk;
          }
          return updated;
        });
      },
      // onDone
      (conversationId) => {
        setIsLoading(false);
        setIsStreaming(false);
        
        if (!currentConversation) {
          // Reload conversations to get the new one
          loadConversations().then(() => {
            setCurrentConversation({ id: conversationId });
          });
        }
      },
      // onError
      (error) => {
        setIsLoading(false);
        setIsStreaming(false);
        setMessages(prev => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg.role === 'assistant') {
            lastMsg.content = `Error: ${error}`;
          }
          return updated;
        });
      }
    );
  }, [currentConversation, selectedModel, isLoading, isStreaming]);

  if (authLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-dark-950">
        <div className="text-center">
          <Sparkles className="w-12 h-12 text-primary-500 animate-pulse mx-auto mb-4" />
          <p className="text-dark-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-dark-950">
      <Sidebar
        conversations={conversations}
        currentConversation={currentConversation}
        onSelectConversation={loadConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        onRefresh={loadConversations}
      />

      <main className="flex-1 flex flex-col">
        {/* Chat Header */}
        <header className="h-14 border-b border-dark-800 flex items-center justify-between px-4 bg-dark-900/50 backdrop-blur-xl">
          <div className="flex items-center gap-2">
            <h1 className="font-medium">
              {currentConversation?.title || 'New Chat'}
            </h1>
          </div>
          <div className="flex items-center gap-2 text-sm text-dark-400">
            <span className="px-2 py-1 bg-dark-800 rounded">
              {selectedModel}
            </span>
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-md px-4">
                <div className="w-16 h-16 rounded-2xl gradient-bg flex items-center justify-center mx-auto mb-6">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Welcome to ZeroX AI</h2>
                <p className="text-dark-400 mb-6">
                  Your intelligent AI assistant powered by state-of-the-art open-source models.
                  Start a conversation to explore what I can help you with!
                </p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {[
                    '💻 Help me write code',
                    '📝 Explain a concept',
                    '🔍 Analyze data',
                    '✨ Creative writing',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleSendMessage(suggestion.slice(2).trim())}
                      className="p-3 bg-dark-800 hover:bg-dark-700 rounded-lg text-left transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto py-4 px-4 space-y-4">
              {messages.map((msg, index) => (
                <ChatMessage
                  key={msg.id || index}
                  message={msg}
                  isStreaming={isStreaming && index === messages.length - 1 && msg.role === 'assistant'}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={isLoading}
          model={selectedModel}
          onModelChange={setSelectedModel}
          models={models}
        />
      </main>
    </div>
  );
};

export default Chat;
