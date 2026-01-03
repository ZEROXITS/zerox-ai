import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  MessageSquare, Plus, Settings, LogOut, User, 
  Trash2, ChevronLeft, ChevronRight, Sparkles,
  Crown, Shield, FolderOpen, Users, Code, Zap
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { chatAPI } from '../utils/api';

const Sidebar = ({ 
  conversations = [], 
  currentConversation, 
  onSelectConversation, 
  onNewChat,
  onDeleteConversation,
  onRefresh 
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, isAdmin, isPremium } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      try {
        await chatAPI.deleteConversation(id);
        onDeleteConversation?.(id);
      } catch (err) {
        console.error('Failed to delete conversation:', err);
      }
    }
  };

  const navItems = [
    { path: '/', icon: MessageSquare, label: 'Chat' },
    { path: '/documents', icon: FolderOpen, label: 'Documents' },
    { path: '/workspaces', icon: Users, label: 'Workspaces' },
    { path: '/developer', icon: Code, label: 'Developer' },
  ];

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/' || location.pathname.startsWith('/chat');
    return location.pathname === path;
  };

  return (
    <aside 
      className={`h-screen bg-gray-900 border-r border-gray-800 flex flex-col transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-72'
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              ZeroX AI
            </span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400"
        >
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      {/* Navigation */}
      <div className="p-3 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
              isActive(item.path)
                ? 'bg-cyan-500/20 text-cyan-400'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            } ${collapsed ? 'justify-center' : ''}`}
          >
            <item.icon size={18} />
            {!collapsed && <span className="text-sm">{item.label}</span>}
          </button>
        ))}
      </div>

      {/* New Chat Button (only on chat page) */}
      {(location.pathname === '/' || location.pathname.startsWith('/chat')) && (
        <div className="px-3 pb-3">
          <button
            onClick={onNewChat}
            className={`w-full flex items-center justify-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition ${
              collapsed ? 'px-2' : ''
            }`}
          >
            <Plus size={20} />
            {!collapsed && <span>New Chat</span>}
          </button>
        </div>
      )}

      {/* Conversations List (only on chat page) */}
      {(location.pathname === '/' || location.pathname.startsWith('/chat')) && (
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          {!collapsed && (
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2 px-2">
              Recent Chats
            </p>
          )}
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => onSelectConversation?.(conv)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition group ${
                currentConversation?.id === conv.id
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:bg-gray-800/50 hover:text-white'
              } ${collapsed ? 'justify-center' : ''}`}
            >
              <MessageSquare size={16} className="flex-shrink-0" />
              {!collapsed && (
                <>
                  <span className="flex-1 truncate text-sm">{conv.title}</span>
                  <button
                    onClick={(e) => handleDelete(e, conv.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-700 rounded transition-all"
                  >
                    <Trash2 size={14} className="text-red-400" />
                  </button>
                </>
              )}
            </div>
          ))}
          
          {conversations.length === 0 && !collapsed && (
            <div className="text-center text-gray-600 py-8">
              <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No conversations yet</p>
            </div>
          )}
        </div>
      )}

      {/* Spacer for non-chat pages */}
      {!(location.pathname === '/' || location.pathname.startsWith('/chat')) && (
        <div className="flex-1" />
      )}

      {/* User Section */}
      <div className="p-3 border-t border-gray-800 space-y-2">
        {/* Usage Stats */}
        {!collapsed && user && (
          <div className="bg-gray-800 rounded-lg p-3 mb-2">
            <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
              <span>Daily Usage</span>
              <span>{user.daily_messages || 0} / {isPremium ? '500' : '50'}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1.5">
              <div 
                className="bg-cyan-500 h-1.5 rounded-full transition-all"
                style={{ 
                  width: `${Math.min(((user.daily_messages || 0) / (isPremium ? 500 : 50)) * 100, 100)}%` 
                }}
              />
            </div>
          </div>
        )}

        {/* Admin Link */}
        {isAdmin && (
          <button
            onClick={() => navigate('/admin')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition ${
              collapsed ? 'justify-center' : ''
            }`}
          >
            <Shield size={18} />
            {!collapsed && <span className="text-sm">Admin Panel</span>}
          </button>
        )}

        {/* Settings */}
        <button
          onClick={() => navigate('/settings')}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition ${
            collapsed ? 'justify-center' : ''
          }`}
        >
          <Settings size={18} />
          {!collapsed && <span className="text-sm">Settings</span>}
        </button>

        {/* User Info & Logout */}
        <div className={`flex items-center gap-3 p-2 rounded-lg bg-gray-800 ${
          collapsed ? 'justify-center' : ''
        }`}>
          <div className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center flex-shrink-0">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="w-full h-full rounded-full" />
            ) : (
              <User size={16} className="text-white" />
            )}
          </div>
          {!collapsed && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user?.username}</p>
                <div className="flex items-center gap-1">
                  {isPremium && <Crown size={12} className="text-yellow-500" />}
                  <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors text-gray-400 hover:text-red-400"
              >
                <LogOut size={18} />
              </button>
            </>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
