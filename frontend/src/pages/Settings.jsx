import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, User, Key, Bell, Shield, Save, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Settings = () => {
  const { user, updateProfile } = useAuth();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  
  const [profile, setProfile] = useState({
    fullName: user?.full_name || '',
    avatarUrl: user?.avatar_url || '',
  });

  const handleSaveProfile = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await updateProfile({
        full_name: profile.fullName,
        avatar_url: profile.avatarUrl,
      });
      setSuccess('Profile updated successfully!');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
  ];

  return (
    <div className="min-h-screen bg-dark-950">
      {/* Header */}
      <header className="border-b border-dark-800 bg-dark-900/50 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="font-semibold">Settings</h1>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <nav className="w-48 flex-shrink-0">
            <ul className="space-y-1">
              {tabs.map((tab) => (
                <li key={tab.id}>
                  <button
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary-600/20 text-primary-400'
                        : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200'
                    }`}
                  >
                    <tab.icon size={18} />
                    {tab.label}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          {/* Content */}
          <div className="flex-1">
            {activeTab === 'profile' && (
              <div className="card">
                <h2 className="text-lg font-semibold mb-6">Profile Settings</h2>
                
                {success && (
                  <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
                    {success}
                  </div>
                )}
                
                {error && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                    {error}
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-dark-400 mb-2">Username</label>
                    <input
                      type="text"
                      value={user?.username || ''}
                      disabled
                      className="input bg-dark-800/50 cursor-not-allowed"
                    />
                    <p className="text-xs text-dark-500 mt-1">Username cannot be changed</p>
                  </div>

                  <div>
                    <label className="block text-sm text-dark-400 mb-2">Email</label>
                    <input
                      type="email"
                      value={user?.email || ''}
                      disabled
                      className="input bg-dark-800/50 cursor-not-allowed"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-dark-400 mb-2">Full Name</label>
                    <input
                      type="text"
                      value={profile.fullName}
                      onChange={(e) => setProfile(p => ({ ...p, fullName: e.target.value }))}
                      placeholder="Your full name"
                      className="input"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-dark-400 mb-2">Avatar URL</label>
                    <input
                      type="url"
                      value={profile.avatarUrl}
                      onChange={(e) => setProfile(p => ({ ...p, avatarUrl: e.target.value }))}
                      placeholder="https://example.com/avatar.jpg"
                      className="input"
                    />
                  </div>

                  <button
                    onClick={handleSaveProfile}
                    disabled={loading}
                    className="btn btn-primary flex items-center gap-2"
                  >
                    {loading ? (
                      <Loader2 size={18} className="animate-spin" />
                    ) : (
                      <Save size={18} />
                    )}
                    Save Changes
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'api-keys' && (
              <div className="card">
                <h2 className="text-lg font-semibold mb-6">API Keys</h2>
                <p className="text-dark-400 mb-4">
                  Add your own API keys to use your own quotas. Your keys are encrypted and stored securely.
                </p>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-dark-400 mb-2">Groq API Key</label>
                    <input
                      type="password"
                      placeholder="gsk_..."
                      className="input"
                    />
                    <p className="text-xs text-dark-500 mt-1">
                      Get your free key at{' '}
                      <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer" className="text-primary-400">
                        console.groq.com
                      </a>
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm text-dark-400 mb-2">Hugging Face API Key</label>
                    <input
                      type="password"
                      placeholder="hf_..."
                      className="input"
                    />
                    <p className="text-xs text-dark-500 mt-1">
                      Get your free key at{' '}
                      <a href="https://huggingface.co/settings/tokens" target="_blank" rel="noopener noreferrer" className="text-primary-400">
                        huggingface.co
                      </a>
                    </p>
                  </div>

                  <button className="btn btn-primary flex items-center gap-2">
                    <Save size={18} />
                    Save API Keys
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="card">
                <h2 className="text-lg font-semibold mb-6">Notification Settings</h2>
                <p className="text-dark-400">Coming soon...</p>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="card">
                <h2 className="text-lg font-semibold mb-6">Security Settings</h2>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium mb-2">Change Password</h3>
                    <div className="space-y-3">
                      <input
                        type="password"
                        placeholder="Current password"
                        className="input"
                      />
                      <input
                        type="password"
                        placeholder="New password"
                        className="input"
                      />
                      <input
                        type="password"
                        placeholder="Confirm new password"
                        className="input"
                      />
                      <button className="btn btn-primary">Update Password</button>
                    </div>
                  </div>

                  <div className="pt-6 border-t border-dark-800">
                    <h3 className="font-medium mb-2 text-red-400">Danger Zone</h3>
                    <p className="text-sm text-dark-400 mb-3">
                      Once you delete your account, there is no going back.
                    </p>
                    <button className="btn bg-red-600 hover:bg-red-700 text-white">
                      Delete Account
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
