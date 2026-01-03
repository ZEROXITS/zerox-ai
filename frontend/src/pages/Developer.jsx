import { useState, useEffect } from 'react';
import { 
  Key, Plus, Copy, Trash2, Eye, EyeOff, Code, 
  CheckCircle, XCircle, Clock, Loader2, Terminal
} from 'lucide-react';
import api from '../utils/api';

export default function Developer() {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newKey, setNewKey] = useState({ name: '', permissions: ['chat'], expires_days: null });
  const [createdKey, setCreatedKey] = useState(null);
  const [creating, setCreating] = useState(false);
  const [showKey, setShowKey] = useState({});
  const [usage, setUsage] = useState(null);

  useEffect(() => {
    fetchApiKeys();
    fetchUsage();
  }, []);

  const fetchApiKeys = async () => {
    try {
      const response = await api.get('/developer/keys');
      setApiKeys(response.data);
    } catch (error) {
      console.error('Error fetching API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsage = async () => {
    try {
      const response = await api.get('/developer/usage');
      setUsage(response.data);
    } catch (error) {
      console.error('Error fetching usage:', error);
    }
  };

  const createApiKey = async () => {
    if (!newKey.name.trim()) return;
    
    setCreating(true);
    try {
      const response = await api.post('/developer/keys', newKey);
      setCreatedKey(response.data);
      fetchApiKeys();
    } catch (error) {
      console.error('Error creating API key:', error);
    } finally {
      setCreating(false);
    }
  };

  const deleteApiKey = async (id) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;
    
    try {
      await api.delete(`/developer/keys/${id}`);
      fetchApiKeys();
    } catch (error) {
      console.error('Error deleting API key:', error);
    }
  };

  const revokeApiKey = async (id) => {
    if (!confirm('Revoke this API key? It will no longer work.')) return;
    
    try {
      await api.put(`/developer/keys/${id}/revoke`);
      fetchApiKeys();
    } catch (error) {
      console.error('Error revoking API key:', error);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // Could add a toast notification here
  };

  const togglePermission = (perm) => {
    setNewKey(prev => ({
      ...prev,
      permissions: prev.permissions.includes(perm)
        ? prev.permissions.filter(p => p !== perm)
        : [...prev.permissions, perm]
    }));
  };

  const permissions = [
    { id: 'chat', name: 'Chat', description: 'Access chat completions API' },
    { id: 'models', name: 'Models', description: 'List available models' },
    { id: 'documents', name: 'Documents', description: 'Access documents API' }
  ];

  const codeExample = `import requests

API_KEY = "your_api_key_here"
BASE_URL = "https://your-domain.com/api/v1/developer"

# Chat completion (OpenAI-compatible)
response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    headers={"X-API-Key": API_KEY},
    json={
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "model": "llama-3.1-70b-versatile",
        "temperature": 0.7
    }
)

print(response.json())`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Code className="w-8 h-8 text-cyan-400" />
              Developer API
            </h1>
            <p className="text-gray-400 mt-1">Manage your API keys and access the API</p>
          </div>
          
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New API Key
          </button>
        </div>

        {/* Usage Stats */}
        {usage && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-xl p-4">
              <p className="text-gray-400 text-sm">Total Requests</p>
              <p className="text-2xl font-bold text-white">{usage.total_requests.toLocaleString()}</p>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-4">
              <p className="text-gray-400 text-sm">Active Keys</p>
              <p className="text-2xl font-bold text-cyan-400">{usage.active_keys}</p>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-4">
              <p className="text-gray-400 text-sm">Total Keys</p>
              <p className="text-2xl font-bold text-white">{usage.total_keys}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* API Keys */}
          <div className="bg-gray-800/50 rounded-xl p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Key className="w-5 h-5 text-cyan-400" />
              Your API Keys
            </h3>
            
            {loading ? (
              <div className="text-center py-8">
                <Loader2 className="w-6 h-6 mx-auto text-cyan-400 animate-spin" />
              </div>
            ) : apiKeys.length === 0 ? (
              <div className="text-center py-8">
                <Key className="w-12 h-12 mx-auto text-gray-600 mb-3" />
                <p className="text-gray-400">No API keys yet</p>
                <button
                  onClick={() => setShowCreate(true)}
                  className="mt-3 text-cyan-400 hover:text-cyan-300"
                >
                  Create your first key
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {apiKeys.map(key => (
                  <div
                    key={key.id}
                    className="bg-gray-700/50 rounded-lg p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-white font-medium">{key.name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <code className="text-gray-400 text-sm bg-gray-800 px-2 py-0.5 rounded">
                            {key.key_prefix}...
                          </code>
                          {key.is_active ? (
                            <span className="text-green-400 text-xs flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" /> Active
                            </span>
                          ) : (
                            <span className="text-red-400 text-xs flex items-center gap-1">
                              <XCircle className="w-3 h-3" /> Revoked
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        {key.is_active && (
                          <button
                            onClick={() => revokeApiKey(key.id)}
                            className="p-1.5 text-gray-400 hover:text-yellow-400 transition"
                            title="Revoke"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => deleteApiKey(key.id)}
                          className="p-1.5 text-gray-400 hover:text-red-400 transition"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    
                    <div className="mt-3 flex flex-wrap gap-1">
                      {key.permissions?.map(perm => (
                        <span
                          key={perm}
                          className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded"
                        >
                          {perm}
                        </span>
                      ))}
                    </div>
                    
                    <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                      <span>{key.total_requests} requests</span>
                      {key.last_used && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Last used {new Date(key.last_used).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Code Example */}
          <div className="bg-gray-800/50 rounded-xl p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-cyan-400" />
              Quick Start
            </h3>
            
            <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
              <pre className="text-sm text-gray-300">
                <code>{codeExample}</code>
              </pre>
            </div>
            
            <button
              onClick={() => copyToClipboard(codeExample)}
              className="mt-3 text-cyan-400 hover:text-cyan-300 text-sm flex items-center gap-1"
            >
              <Copy className="w-4 h-4" />
              Copy code
            </button>
            
            <div className="mt-6">
              <h4 className="text-white font-medium mb-2">API Endpoints</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs">POST</span>
                  <code className="text-gray-400">/api/v1/developer/v1/chat/completions</code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">GET</span>
                  <code className="text-gray-400">/api/v1/developer/v1/models</code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Create API Key Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-xl font-bold text-white mb-4">Create API Key</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">Name</label>
                <input
                  type="text"
                  value={newKey.name}
                  onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
                  placeholder="My App"
                  className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-2">Permissions</label>
                <div className="space-y-2">
                  {permissions.map(perm => (
                    <label
                      key={perm.id}
                      className="flex items-center gap-3 p-2 bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-700 transition"
                    >
                      <input
                        type="checkbox"
                        checked={newKey.permissions.includes(perm.id)}
                        onChange={() => togglePermission(perm.id)}
                        className="w-4 h-4 rounded border-gray-500 text-cyan-500 focus:ring-cyan-500"
                      />
                      <div>
                        <p className="text-white text-sm">{perm.name}</p>
                        <p className="text-gray-400 text-xs">{perm.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Expiration (optional)</label>
                <select
                  value={newKey.expires_days || ''}
                  onChange={(e) => setNewKey({ ...newKey, expires_days: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="">Never expires</option>
                  <option value="7">7 days</option>
                  <option value="30">30 days</option>
                  <option value="90">90 days</option>
                  <option value="365">1 year</option>
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreate(false);
                  setCreatedKey(null);
                }}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
              >
                Cancel
              </button>
              <button
                onClick={createApiKey}
                disabled={creating || !newKey.name.trim()}
                className="flex-1 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50 transition"
              >
                {creating ? (
                  <Loader2 className="w-5 h-5 mx-auto animate-spin" />
                ) : (
                  'Create'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Created Key Modal */}
      {createdKey && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md mx-4">
            <div className="text-center mb-4">
              <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-2" />
              <h3 className="text-xl font-bold text-white">API Key Created!</h3>
              <p className="text-gray-400 text-sm mt-1">
                Make sure to copy your key now. You won't be able to see it again!
              </p>
            </div>
            
            <div className="bg-gray-900 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between gap-2">
                <code className="text-cyan-400 text-sm break-all">
                  {createdKey.key}
                </code>
                <button
                  onClick={() => copyToClipboard(createdKey.key)}
                  className="p-2 text-gray-400 hover:text-white transition flex-shrink-0"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <button
              onClick={() => {
                setCreatedKey(null);
                setShowCreate(false);
                setNewKey({ name: '', permissions: ['chat'], expires_days: null });
              }}
              className="w-full px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
