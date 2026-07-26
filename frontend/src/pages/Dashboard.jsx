import React, { useState, useEffect } from 'react';
import { Package, AlertTriangle, ShieldCheck, Activity, Info } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({ total: 0, fresh: 0, warning: 0, spoiled: 0 });
  const [inventory, setInventory] = useState([]);
  
  useEffect(() => {
    // Fetch inventory to compute real analytics
    const fetchInventory = async () => {
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
        const response = await fetch(`${API_URL}/api/inventory`);
        if (response.ok) {
          const data = await response.json();
          setInventory(data);
          
          let fresh = 0, warning = 0, spoiled = 0;
          data.forEach(item => {
            if (item.status === 'Fresh') fresh++;
            else if (item.status === 'Near Expiry' || item.status === 'Warning') warning++;
            else spoiled++;
          });
          
          setStats({ total: data.length, fresh, warning, spoiled });
        }
      } catch (error) {
        console.error("Error fetching analytics data:", error);
      }
    };
    fetchInventory();
  }, []);

  const pieData = [
    { name: 'Fresh', value: stats.fresh, color: '#10b981' },
    { name: 'Near Expiry', value: stats.warning, color: '#f59e0b' },
    { name: 'Spoiled', value: stats.spoiled, color: '#ef4444' }
  ];

  // Group inventory by category for bar chart
  const categoryData = inventory.reduce((acc, item) => {
    const existing = acc.find(x => x.category === item.category);
    if (existing) {
      existing.count += 1;
      existing.avgScore = ((existing.avgScore * (existing.count - 1)) + item.score) / existing.count;
    } else {
      acc.push({ category: item.category, count: 1, avgScore: item.score });
    }
    return acc;
  }, []);

  return (
    <div className="dashboard-container">
      <div className="stats-grid">
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6' }}>
            <Package size={24} />
          </div>
          <div className="stat-info">
            <h3>Total Scanned</h3>
            <p>{stats.total}</p>
          </div>
        </div>
        
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>
            <ShieldCheck size={24} />
          </div>
          <div className="stat-info">
            <h3>Fresh Items</h3>
            <p>{stats.fresh}</p>
          </div>
        </div>
        
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b' }}>
            <Activity size={24} />
          </div>
          <div className="stat-info">
            <h3>Near Expiry</h3>
            <p>{stats.warning}</p>
          </div>
        </div>
        
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>
            <AlertTriangle size={24} />
          </div>
          <div className="stat-info">
            <h3>Spoiled</h3>
            <p>{stats.spoiled}</p>
          </div>
        </div>
      </div>

      <div className="charts-section" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
        <div className="glass-card chart-container" style={{ padding: '24px' }}>
          <h3 style={{ marginBottom: '20px', fontSize: '1.2rem' }}>Freshness Distribution</h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'rgba(30,41,59,0.9)', border: 'none', borderRadius: '8px', color: '#fff' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card chart-container" style={{ padding: '24px' }}>
          <h3 style={{ marginBottom: '20px', fontSize: '1.2rem' }}>Average Score by Category</h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={categoryData}>
                <XAxis dataKey="category" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: 'rgba(30,41,59,0.9)', border: 'none', borderRadius: '8px', color: '#fff' }} cursor={{fill: 'rgba(255,255,255,0.05)'}} />
                <Bar dataKey="avgScore" name="Avg Freshness %" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="glass-card insights-card" style={{ marginTop: '24px', padding: '24px', backgroundColor: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <Info size={24} color="#3b82f6" />
          <h3 style={{ margin: 0, color: '#3b82f6' }}>AI Inventory Insights</h3>
        </div>
        <ul style={{ listStyleType: 'disc', paddingLeft: '24px', color: '#e2e8f0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <li><strong>{stats.warning} items</strong> are nearing expiration and should be prioritized for use or discounted.</li>
          <li><strong>{stats.spoiled} items</strong> have reached full spoilage. Please route these to composting or biogas processing according to disposal guidelines.</li>
          <li>Overall inventory health is at <strong>{stats.total > 0 ? Math.round((stats.fresh / stats.total) * 100) : 0}%</strong> optimal freshness.</li>
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;
