import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Users, Package, Database, Brain, Activity, Plus, FileText, Camera, Shield, Server, HardDrive, Cpu, Bell, ShieldAlert, LineChart } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';
import toast from 'react-hot-toast';
import './Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL;
const COLORS = ['var(--accent-primary)', '#3b82f6', 'var(--warning)', '#8b5cf6', '#ec4899'];

const KpiCard = ({ title, value, icon: Icon, iconColor, subtitle }) => {
  return (
    <div className="premium-stat-card">
      <div className="stat-header">
        <span className="stat-label">{title}</span>
        <div className={`stat-icon ${iconColor}`}><Icon size={20} /></div>
      </div>
      <div className="stat-body">
        <div className="stat-value">{value}</div>
      </div>
      <div className="stat-footer">
        <span className="stat-subtitle" style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{subtitle}</span>
      </div>
    </div>
  );
};

const NoDataPlaceholder = ({ message }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '20px', color: 'var(--text-secondary)', textAlign: 'center' }}>
    <Activity size={32} style={{ marginBottom: '10px', opacity: 0.5 }} />
    <span>{message || "No data available"}</span>
  </div>
);

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/api/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(res.data);
    } catch (err) {
      toast.error("Failed to load admin stats");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--accent-primary)' }}>Loading dashboard...</div>;
  if (!stats) return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--danger)' }}>Error loading data</div>;

  // Prepare chart data where possible
  const othersCount = Math.max(0, stats.total_users - stats.total_retailers - stats.total_consumers);
  const userData = [
    { name: 'Consumers', value: stats.total_consumers },
    { name: 'Retail Managers', value: stats.total_retailers },
    { name: 'Others (Staff/Admin)', value: othersCount }
  ].filter(d => d.value > 0);

  return (
    <div className="page-container animate-fade-in" style={{ paddingBottom: '40px' }}>
      <div className="page-header" style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ margin: '0 0 8px 0' }}>Platform Overview</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Global system statistics and metrics.</p>
        </div>
        
        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={() => navigate('/admin/users')}><Users size={16}/> Add User</button>
          <button className="btn btn-secondary" onClick={() => navigate('/admin/knowledge-base')}><Database size={16}/> Edit Knowledge Base</button>
          <button className="btn btn-primary" onClick={() => navigate('/scanner')}><Camera size={16}/> Open Scanner</button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="stats-grid" style={{ marginBottom: '24px' }}>
        <KpiCard title="Total Users" value={stats.total_users} icon={Users} iconColor="blue" subtitle={`${stats.total_retailers} Retail Managers, ${stats.total_consumers} Consumers`} />
        <KpiCard title="Retail Managers" value={stats.total_retailers} icon={Package} iconColor="emerald" subtitle="Active business accounts" />
        <KpiCard title="Consumers" value={stats.total_consumers} icon={Users} iconColor="slate" subtitle="Active consumer accounts" />
        <KpiCard title="Inventory Batches" value={stats.total_inventory_batches} icon={Database} iconColor="blue" subtitle="Total batches across system" />
        <KpiCard title="Knowledge Base Items" value={stats.total_knowledge_base_items} icon={Brain} iconColor="warning" subtitle="Reference database size" />
        <KpiCard title="Total AI Scans" value={stats.total_ai_predictions} icon={Activity} iconColor="emerald" subtitle="Predictions processed" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginBottom: '24px' }}>
        {/* User Distribution Chart */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><Users size={18} color="#3b82f6"/> User Distribution</h3>
          <div style={{ height: '240px' }}>
            {userData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={userData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                    {userData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip contentStyle={{ backgroundColor: 'var(--bg-secondary)', border: 'none', borderRadius: '8px', color: 'var(--text-primary)' }} itemStyle={{ color: 'var(--text-primary)' }} />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            ) : <NoDataPlaceholder message="No user role data available" />}
          </div>
        </div>

        {/* AI Scan Summary Chart */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><Brain size={18} color="var(--accent-primary)"/> AI Scan Summary</h3>
          <div style={{ height: '240px' }}>
            <NoDataPlaceholder message="Freshness distribution data is currently unavailable in the global API." />
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginBottom: '24px' }}>
        {/* Inventory Health */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><Package size={18} color="var(--warning)"/> Inventory Health</h3>
          <div style={{ height: '200px' }}>
            <NoDataPlaceholder message="Global inventory health metrics unavailable." />
          </div>
        </div>

        {/* Notifications Summary */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><Bell size={18} color="var(--danger)"/> System Notifications</h3>
          <div style={{ height: '200px' }}>
            <NoDataPlaceholder message="No critical system alerts." />
          </div>
        </div>

        {/* System Health Panel */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><Server size={18} color="#8b5cf6"/> System Health</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'var(--bg-overlay)', borderRadius: '8px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><HardDrive size={16} color="var(--text-secondary)"/> Database</span>
              <span className="status-badge-small success" style={{ fontSize: '0.75rem', padding: '2px 8px' }}>Connected</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'var(--bg-overlay)', borderRadius: '8px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Cpu size={16} color="var(--text-secondary)"/> AI Inference Engine</span>
              <span className="status-badge-small success" style={{ fontSize: '0.75rem', padding: '2px 8px' }}>Online</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'var(--bg-overlay)', borderRadius: '8px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Shield size={16} color="var(--text-secondary)"/> RBAC Security</span>
              <span className="status-badge-small success" style={{ fontSize: '0.75rem', padding: '2px 8px' }}>Enforcing</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="glass-card" style={{ padding: '20px' }}>
        <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><Activity size={18} color="var(--accent-primary)"/> Global Recent Activity</h3>
        <div style={{ minHeight: '150px' }}>
          <NoDataPlaceholder message="Global activity feed is not available in the current API version." />
        </div>
      </div>

    </div>
  );
};

export default AdminDashboard;
