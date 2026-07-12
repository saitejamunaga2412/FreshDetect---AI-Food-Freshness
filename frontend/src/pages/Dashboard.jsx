import React from 'react';
import { Package, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';
import './Dashboard.css';

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      <div className="stats-grid">
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6' }}>
            <Package size={24} />
          </div>
          <div className="stat-info">
            <h3>Total Items</h3>
            <p>1,248</p>
          </div>
        </div>
        
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>
            <ShieldCheck size={24} />
          </div>
          <div className="stat-info">
            <h3>Fresh Items</h3>
            <p>982</p>
          </div>
        </div>
        
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b' }}>
            <Activity size={24} />
          </div>
          <div className="stat-info">
            <h3>Warning Items</h3>
            <p>154</p>
          </div>
        </div>
        
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>
            <AlertTriangle size={24} />
          </div>
          <div className="stat-info">
            <h3>Spoiled Items</h3>
            <p>112</p>
          </div>
        </div>
      </div>

      <div className="charts-section">
        <div className="glass-card chart-container">
          <h3>Recent Inventory Scans</h3>
          <div className="placeholder-chart">
            <p>Chart data will be visualized here</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
