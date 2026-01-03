import { useState, useEffect } from 'react';
import { 
  Users, Plus, Settings, Trash2, UserPlus, LogOut,
  MessageSquare, Crown, Shield, User, Loader2
} from 'lucide-react';
import api from '../utils/api';

export default function Workspaces() {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);
  const [members, setMembers] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [newWorkspace, setNewWorkspace] = useState({ name: '', description: '' });
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [creating, setCreating] = useState(false);
  const [addingMember, setAddingMember] = useState(false);

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  useEffect(() => {
    if (selectedWorkspace) {
      fetchMembers(selectedWorkspace.id);
      fetchConversations(selectedWorkspace.id);
    }
  }, [selectedWorkspace]);

  const fetchWorkspaces = async () => {
    try {
      const response = await api.get('/workspaces/');
      setWorkspaces(response.data);
      if (response.data.length > 0 && !selectedWorkspace) {
        setSelectedWorkspace(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching workspaces:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMembers = async (workspaceId) => {
    try {
      const response = await api.get(`/workspaces/${workspaceId}/members`);
      setMembers(response.data);
    } catch (error) {
      console.error('Error fetching members:', error);
    }
  };

  const fetchConversations = async (workspaceId) => {
    try {
      const response = await api.get(`/workspaces/${workspaceId}/conversations`);
      setConversations(response.data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const createWorkspace = async () => {
    if (!newWorkspace.name.trim()) return;
    
    setCreating(true);
    try {
      const response = await api.post('/workspaces/', newWorkspace);
      setWorkspaces([...workspaces, response.data]);
      setSelectedWorkspace(response.data);
      setShowCreate(false);
      setNewWorkspace({ name: '', description: '' });
    } catch (error) {
      console.error('Error creating workspace:', error);
    } finally {
      setCreating(false);
    }
  };

  const deleteWorkspace = async (id) => {
    if (!confirm('Are you sure you want to delete this workspace?')) return;
    
    try {
      await api.delete(`/workspaces/${id}`);
      setWorkspaces(workspaces.filter(w => w.id !== id));
      if (selectedWorkspace?.id === id) {
        setSelectedWorkspace(workspaces[0] || null);
      }
    } catch (error) {
      console.error('Error deleting workspace:', error);
    }
  };

  const addMember = async () => {
    if (!newMemberEmail.trim() || !selectedWorkspace) return;
    
    setAddingMember(true);
    try {
      await api.post(`/workspaces/${selectedWorkspace.id}/members`, {
        email: newMemberEmail,
        role: 'member'
      });
      fetchMembers(selectedWorkspace.id);
      setNewMemberEmail('');
    } catch (error) {
      console.error('Error adding member:', error);
      alert(error.response?.data?.detail || 'Error adding member');
    } finally {
      setAddingMember(false);
    }
  };

  const removeMember = async (userId) => {
    if (!confirm('Remove this member?')) return;
    
    try {
      await api.delete(`/workspaces/${selectedWorkspace.id}/members/${userId}`);
      fetchMembers(selectedWorkspace.id);
    } catch (error) {
      console.error('Error removing member:', error);
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'admin':
        return <Shield className="w-4 h-4 text-cyan-500" />;
      default:
        return <User className="w-4 h-4 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Users className="w-8 h-8 text-cyan-400" />
              Workspaces
            </h1>
            <p className="text-gray-400 mt-1">Collaborate with your team</p>
          </div>
          
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Workspace
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Workspaces List */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800/50 rounded-xl p-4">
              <h3 className="text-white font-semibold mb-3">Your Workspaces</h3>
              
              {workspaces.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No workspaces yet</p>
              ) : (
                <div className="space-y-2">
                  {workspaces.map(workspace => (
                    <div
                      key={workspace.id}
                      onClick={() => setSelectedWorkspace(workspace)}
                      className={`p-3 rounded-lg cursor-pointer transition ${
                        selectedWorkspace?.id === workspace.id
                          ? 'bg-cyan-500/20 border border-cyan-500'
                          : 'bg-gray-700/50 hover:bg-gray-700 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{workspace.name}</p>
                          <p className="text-gray-400 text-sm">
                            {workspace.member_count} members
                          </p>
                        </div>
                        <Users className="w-4 h-4 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Workspace Details */}
          <div className="lg:col-span-3">
            {selectedWorkspace ? (
              <div className="space-y-6">
                {/* Workspace Header */}
                <div className="bg-gray-800/50 rounded-xl p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-white">
                        {selectedWorkspace.name}
                      </h2>
                      {selectedWorkspace.description && (
                        <p className="text-gray-400 mt-1">
                          {selectedWorkspace.description}
                        </p>
                      )}
                      <p className="text-gray-500 text-sm mt-2">
                        Created {new Date(selectedWorkspace.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteWorkspace(selectedWorkspace.id)}
                      className="p-2 text-gray-400 hover:text-red-400 transition"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Members */}
                  <div className="bg-gray-800/50 rounded-xl p-6">
                    <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                      <Users className="w-5 h-5 text-cyan-400" />
                      Members ({members.length})
                    </h3>
                    
                    {/* Add Member */}
                    <div className="flex gap-2 mb-4">
                      <input
                        type="email"
                        value={newMemberEmail}
                        onChange={(e) => setNewMemberEmail(e.target.value)}
                        placeholder="Email address"
                        className="flex-1 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      />
                      <button
                        onClick={addMember}
                        disabled={addingMember}
                        className="px-3 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50 transition"
                      >
                        {addingMember ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <UserPlus className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                    
                    {/* Members List */}
                    <div className="space-y-2 max-h-[300px] overflow-y-auto">
                      {members.map(member => (
                        <div
                          key={member.id}
                          className="flex items-center justify-between p-2 bg-gray-700/50 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            {member.avatar_url ? (
                              <img
                                src={member.avatar_url}
                                alt={member.username}
                                className="w-8 h-8 rounded-full"
                              />
                            ) : (
                              <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                                <span className="text-white text-sm">
                                  {member.username[0].toUpperCase()}
                                </span>
                              </div>
                            )}
                            <div>
                              <p className="text-white text-sm">{member.username}</p>
                              <p className="text-gray-400 text-xs">{member.email}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getRoleIcon(member.role)}
                            {member.role !== 'owner' && (
                              <button
                                onClick={() => removeMember(member.id)}
                                className="p-1 text-gray-400 hover:text-red-400 transition"
                              >
                                <LogOut className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Conversations */}
                  <div className="bg-gray-800/50 rounded-xl p-6">
                    <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                      <MessageSquare className="w-5 h-5 text-cyan-400" />
                      Conversations ({conversations.length})
                    </h3>
                    
                    <div className="space-y-2 max-h-[350px] overflow-y-auto">
                      {conversations.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">
                          No conversations yet
                        </p>
                      ) : (
                        conversations.map(conv => (
                          <div
                            key={conv.id}
                            className="p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition cursor-pointer"
                          >
                            <p className="text-white font-medium truncate">
                              {conv.title}
                            </p>
                            <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                              <span>{conv.model}</span>
                              <span>•</span>
                              <span>
                                {new Date(conv.updated_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-gray-800/50 rounded-xl p-12 text-center">
                <Users className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                <h3 className="text-xl text-white mb-2">No Workspace Selected</h3>
                <p className="text-gray-400 mb-4">
                  Select a workspace or create a new one
                </p>
                <button
                  onClick={() => setShowCreate(true)}
                  className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition"
                >
                  Create Workspace
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Workspace Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-xl font-bold text-white mb-4">Create Workspace</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">Name</label>
                <input
                  type="text"
                  value={newWorkspace.name}
                  onChange={(e) => setNewWorkspace({ ...newWorkspace, name: e.target.value })}
                  placeholder="My Team"
                  className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Description (optional)</label>
                <textarea
                  value={newWorkspace.description}
                  onChange={(e) => setNewWorkspace({ ...newWorkspace, description: e.target.value })}
                  placeholder="What's this workspace for?"
                  rows={3}
                  className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-cyan-500 resize-none"
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreate(false)}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
              >
                Cancel
              </button>
              <button
                onClick={createWorkspace}
                disabled={creating || !newWorkspace.name.trim()}
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
    </div>
  );
}
