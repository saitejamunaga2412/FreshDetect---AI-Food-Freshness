import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Filter, Shield } from 'lucide-react';
import toast from 'react-hot-toast';

const API_URL = import.meta.env.VITE_API_URL;

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(res.data);
    } catch (err) {
      toast.error("Failed to fetch users");
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = (user.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
                           user.email?.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesRole = roleFilter === 'All' || user.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header" style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: '0 0 8px 0' }}>User Management</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>View and filter registered accounts.</p>
        </div>
      </div>

      <div className="filters-bar" style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
        <div className="search-box" style={{ display: 'flex', alignItems: 'center', background: 'var(--border-subtle)', padding: '8px 16px', borderRadius: '8px', flex: 1, border: '1px solid var(--border-strong)' }}>
          <Search size={18} color="var(--text-secondary)" style={{ marginRight: '12px' }} />
          <input 
            type="text" 
            placeholder="Search by name or email..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', width: '100%', outline: 'none' }}
          />
        </div>
        <div className="filter-select" style={{ display: 'flex', alignItems: 'center', background: 'var(--border-subtle)', padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-strong)' }}>
          <Filter size={18} color="var(--text-secondary)" style={{ marginRight: '12px' }} />
          <select 
            value={roleFilter} 
            onChange={(e) => setRoleFilter(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', cursor: 'pointer' }}
          >
            <option value="All" style={{ background: 'var(--bg-secondary)' }}>All Roles</option>
            <option value="Admin" style={{ background: 'var(--bg-secondary)' }}>Admin</option>
            <option value="Retailer" style={{ background: 'var(--bg-secondary)' }}>Retailer</option>
            <option value="Consumer" style={{ background: 'var(--bg-secondary)' }}>Consumer</option>
          </select>
        </div>
      </div>

      <div className="table-container" style={{ overflowX: 'auto', background: 'var(--glass-bg)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-strong)', textAlign: 'left', color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>
              <th style={{ padding: '16px' }}>Name</th>
              <th style={{ padding: '16px' }}>Email</th>
              <th style={{ padding: '16px' }}>Role</th>
              <th style={{ padding: '16px' }}>Joined Date</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="4" style={{ padding: '24px', textAlign: 'center' }}>Loading users...</td></tr>
            ) : filteredUsers.length === 0 ? (
              <tr><td colSpan="4" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>No users found matching criteria.</td></tr>
            ) : (
              filteredUsers.map(user => (
                <tr key={user.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '16px', color: 'var(--text-primary)' }}>{user.name}</td>
                  <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>{user.email}</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{ 
                      display: 'inline-flex', alignItems: 'center', gap: '6px', 
                      padding: '4px 10px', borderRadius: '12px', fontSize: '0.8rem',
                      background: user.role === 'Admin' ? 'rgba(239, 68, 68, 0.1)' : user.role === 'Retailer' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(59, 130, 246, 0.1)',
                      color: user.role === 'Admin' ? 'var(--danger)' : user.role === 'Retailer' ? 'var(--accent-primary)' : '#3b82f6'
                    }}>
                      {user.role === 'Admin' && <Shield size={14} />}
                      {user.role}
                    </span>
                  </td>
                  <td style={{ padding: '16px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    {new Date(user.createdAt).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminUsers;
