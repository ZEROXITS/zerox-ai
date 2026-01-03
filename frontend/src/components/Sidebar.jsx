import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MessageSquare, Plus, Settings, LogOut, User, 
  Trash2, ChevronLeft, ChevronRight, Sparkles,
  Crown, Shield
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { chatAPI } from '../utils/api';
import clsx from 'clsx';

const Sidebar = ({ 
  conversations, 
  currentConversation, 
  onSelectConversation, 
  onNewChat,
  onDeleteConversation,
  onRefresh 
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, isAdmin, isPremium } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      try {
        await chatAPI.deleteConversation(id);
        onDeleteConversation(id);
      } catch (err) {
        console.error('Failed to delete conversation:', err);
      }
    }
  };

  return (
    <aside 
      className={clsx(
        'h-screen bg-dark-900 border-r border-dark-800 flex flex-col transition-all duration-300',
        collapsed ? 'w-16' : 'w-72'
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-dark-800 flex items-center justify-between">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg gradient-text">ZeroX AI</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
        >
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className={clsx(
            'btn btn-primary w-full flex items-center justify-center gap-2',
            collapsed && 'px-2'
          )}
        >
          <Plus size={20} />
          {!collapsed && <span>New Chat</span>}
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            onClick={() => onSelectConversation(conv)}
            className={clsx(
              'sidebar-item group',
              currentConversation?.id === conv.id && 'active'
            )}
          >
            <MessageSquare size={18} className="flex-shrink-0" />
            {!collapsed && (
              <>
                <span className="flex-1 truncate text-sm">{conv.title}</span>
                <button
                  onClick={(e) => handleDelete(e, conv.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-dark-700 rounded transition-all"
                >
                  <Trash2 size={14} className="text-red-400" />
                </button>
              </>
            )}
          </div>
        ))}
        
        {conversations.length === 0 && !collapsed && (
          <div className="text-center text-dark-500 py-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No conversations yet</p>
            <p className="text-xs">Start a new chat!</p>
          </div>
        )}
      </div>

      {/* User Section */}
      <div className="p-3 border-t border-dark-800 space-y-2">
        {/* Usage Stats */}
        {!collapsed && user && (
          <div className="bg-dark-800 rounded-lg p-3 mb-2">
            <div className="flex items-center justify-between text-xs text-dark-400 mb-1">
              <span>Daily Usage</span>
              <span>{user.daily_messages} / {isPremium ? '500' : '50'}</span>
            </div>
            <div className="w-full bg-dark-700 rounded-full h-1.5">
              <div 
                className="bg-primary-500 h-1.5 rounded-full transition-all"
                style={{ 
                  width: `${Math.min((user.daily_messages / (isPremium ? 500 : 50)) * 100, 100)}%` 
                }}
              />
            </div>
          </div>
        )}

        {/* Admin Link */}
        {isAdmin && (
          <button
            onClick={() => navigate('/admin')}
            className={clsx('sidebar-item w-full', collapsed && 'justify-center')}
          >
            <Shield size={18} />
            {!collapsed && <span>Admin Panel</span>}
          </button>
        )}

        {/* Settings */}
        <button
          onClick={() => navigate('/settings')}
          className={clsx('sidebar-item w-full', collapsed && 'justify-center')}
        >
          <Settings size={18} />
          {!collapsed && <span>Settings</span>}
        </button>

        {/* User Info & Logout */}
        <div className={clsx(
          'flex items-center gap-3 p-2 rounded-lg bg-dark-800',
          collapsed && 'justify-center'
        )}>
          <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center flex-shrink-0">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="w-full h-full rounded-full" />
            ) : (
              <User size={16} />
            )}
          </div>
          {!collapsed && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.username}</p>
                <div className="flex items-center gap-1">
                  {isPremium && <Crown size={12} className="text-yellow-500" />}
                  <p className="text-xs text-dark-400 capitalize">{user?.role}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-red-400"
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
