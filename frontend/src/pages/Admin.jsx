import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Users, MessageSquare, Activity, 
  Crown, Shield, Trash2, Ban, Check 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../utils/api';

const Admin = () => {
  const { isAdmin } = useAuth();
  const navigate = useNavigate();
  
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAdmin) {
      navigate('/');
      return;
    }
    loadData();
  }, [isAdmin, navigate]);

  const loadData = async () => {
    try {
      const [statsRes, usersRes] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getUsers(),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId, role) => {
    try {
      await adminAPI.updateUserRole(userId, role);
      setUsers(prev => prev.map(u => 
        u.id === userId ? { ...u, role } : u
      ));
    } catch (err) {
      console.error('Failed to update role:', err);
    }
  };

  const handleToggleStatus = async (userId) => {
    try {
      await adminAPI.toggleUserStatus(userId);
      setUsers(prev => prev.map(u => 
        u.id === userId ? { ...u, is_active: !u.is_active } : u
      ));
    } catch (err) {
      console.error('Failed to toggle status:', err);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await adminAPI.deleteUser(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950">
      {/* Header */}
      <header className="border-b border-dark-800 bg-dark-900/50 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <Shield className="text-primary-500" size={20} />
          <h1 className="font-semibold">Admin Dashboard</h1>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="card flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <Users className="text-blue-500" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.total_users || 0}</p>
              <p className="text-sm text-dark-400">Total Users</p>
            </div>
          </div>

          <div className="card flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
              <Activity className="text-green-500" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.active_users || 0}</p>
              <p className="text-sm text-dark-400">Active Users</p>
            </div>
          </div>

          <div className="card flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <MessageSquare className="text-purple-500" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.total_messages || 0}</p>
              <p className="text-sm text-dark-400">Total Messages</p>
            </div>
          </div>

          <div className="card flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-orange-500/20 flex items-center justify-center">
              <MessageSquare className="text-orange-500" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats?.messages_today || 0}</p>
              <p className="text-sm text-dark-400">Messages Today</p>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Users</h2>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-800">
                  <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">User</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Role</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Messages</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-dark-800/50 hover:bg-dark-800/30">
                    <td className="py-3 px-4">
                      <div>
                        <p className="font-medium">{user.username}</p>
                        <p className="text-sm text-dark-400">{user.email}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        className="bg-dark-800 border border-dark-700 rounded px-2 py-1 text-sm"
                      >
                        <option value="user">User</option>
                        <option value="premium">Premium</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm">{user.total_messages}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${
                        user.is_active 
                          ? 'bg-green-500/20 text-green-400' 
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {user.is_active ? <Check size={12} /> : <Ban size={12} />}
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleStatus(user.id)}
                          className="p-1.5 hover:bg-dark-700 rounded transition-colors"
                          title={user.is_active ? 'Deactivate' : 'Activate'}
                        >
                          <Ban size={16} className={user.is_active ? 'text-orange-400' : 'text-green-400'} />
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.id)}
                          className="p-1.5 hover:bg-dark-700 rounded transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={16} className="text-red-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Admin;
