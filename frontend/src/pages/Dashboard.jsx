import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { 
  Package, AlertTriangle, ShieldCheck, Activity, LineChart as LineChartIcon,
  List, Clock, CheckCircle2, Zap, Brain, Server, Database, Camera, Bell, 
  TrendingUp, TrendingDown, Minus, Info, AlertCircle
} from 'lucide-react';
import './Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL;
const COLORS = ['var(--accent-primary)', 'var(--warning)', 'var(--danger)', '#3b82f6', '#8b5cf6', '#ec4899'];

// Reusable Framer Motion Variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

// Reusable Components
const KpiCard = React.memo(({ title, value, icon: Icon, iconColor, trend, trendValue, subtitle, isPrimary }) => {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendClass = trend === 'up' ? 'text-emerald' : trend === 'down' ? 'text-danger' : 'text-slate';

  return (
    <motion.div 
      className={`premium-stat-card ${isPrimary ? 'health-card' : ''}`} 
      whileHover={{ y: -4, boxShadow: "0 10px 30px var(--bg-overlay-hover)" }}
    >
      <div className="stat-header">
        <span className="stat-label">{title}</span>
        <div className={`stat-icon ${iconColor}`}><Icon size={20} aria-hidden="true"/></div>
      </div>
      <div className="stat-body">
        {value === null || value === undefined ? (
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: '500', marginTop: '5px' }}>
             No data yet
          </div>
        ) : (
          <div className="stat-value">
            <NumberCounter targetValue={value} />
            {title.includes('%') ? '%' : ''}
          </div>
        )}
      </div>
      <div className="stat-footer">
        {trendValue && (
          <span className={`stat-trend ${trendClass}`} aria-label={`Trend ${trend}`}>
            <TrendIcon size={14} /> {trendValue}
          </span>
        )}
        <span className="stat-subtitle">{subtitle}</span>
      </div>
    </motion.div>
  );
});

// Simple animated number counter
const NumberCounter = ({ targetValue }) => {
  const [value, setValue] = useState(0);
  
  useEffect(() => {
    let start = 0;
    const end = parseInt(targetValue) || 0;
    if (start === end) {
      setValue(end);
      return;
    }
    
    let totalDuration = 1000;
    let incrementTime = (totalDuration / Math.max(end, 1));
    
    let timer = setInterval(() => {
      start += 1;
      if (start >= end) {
        setValue(end);
        clearInterval(timer);
      } else {
        setValue(start);
      }
    }, incrementTime);
    
    return () => clearInterval(timer);
  }, [targetValue]);
  
  return <span>{targetValue > 0 ? value : targetValue}</span>;
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const userRes = await axios.get(`${API_URL}/api/auth/me`, { headers: { 'Authorization': `Bearer ${token}` } }).catch(() => ({ data: null }));
      
      if (userRes && userRes.data) {
        setUser(userRes.data);
        
        if (userRes.data.role === 'Retailer' || userRes.data.role === 'Admin') {
          // Fetch from the newly aggregated reports API
          const reportRes = await axios.get(`${API_URL}/api/reports/comprehensive`, { headers: { 'Authorization': `Bearer ${token}` } });
          const { summary, data } = reportRes.data;
          
          setStats({
            isRetailer: true,
            summary,
            data
          });
        }
      }
    } catch (err) {
      console.error(err);
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour >= 5 && hour < 12) return 'Good Morning';
    if (hour >= 12 && hour < 17) return 'Good Afternoon';
    if (hour >= 17 && hour < 21) return 'Good Evening';
    return 'Good Night';
  };

  if (loading) {
    return (
      <div className="dashboard-container" aria-busy="true" aria-label="Loading dashboard">
        <div className="skeleton-header"></div>
        <div className="stats-grid">
          {[1,2,3,4,5,6,7,8].map(i => <div key={i} className="premium-stat-card skeleton-box" style={{height: 140}}></div>)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state" role="alert">
        <AlertTriangle size={48} color="var(--danger)" />
        <h2>{error}</h2>
        <button className="btn btn-primary" onClick={fetchStats}>Retry</button>
      </div>
    );
  }

  // Precompute KPI Values
  const totalBatches = stats?.summary?.inventory?.total_items || 0;
  const activeBatches = stats?.summary?.inventory?.total_items || 0; // The comprehensive endpoint only fetches active by default
  const highRisk = stats?.data?.batches?.filter(b => b.risk_forecast === 'High Risk').length || 0;
  const criticalNotifs = stats?.summary?.notifications?.CRITICAL || 0;
  const compliantTotal = stats?.summary?.storage?.Compliant || 0;
  const compliancePct = totalBatches > 0 ? Math.round((compliantTotal / totalBatches) * 100) : 0;
  const avgDaysRem = totalBatches > 0 
    ? Math.round(stats?.data?.batches?.reduce((acc, b) => acc + (b.days_remaining || 0), 0) / totalBatches) 
    : 0;

  // Chart Rendering Helpers
  const renderPieChart = (dataObj, title) => {
    const dataArr = Object.keys(dataObj).map(k => ({ name: k, value: dataObj[k] })).filter(d => d.value > 0);
    if(dataArr.length === 0) return (
        <div className="empty-state chart-empty">
          <PieChart size={32} opacity={0.5}/> 
          <span>No data to display.</span>
        </div>
    );
    
    return (
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie
              data={dataArr}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
              animationDuration={1500}
            >
              {dataArr.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <RechartsTooltip 
              contentStyle={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-strong)', borderRadius: '8px', color: 'var(--text-primary)' }}
            />
            <Legend verticalAlign="bottom" height={36} iconType="circle"/>
          </PieChart>
        </ResponsiveContainer>
    );
  };

  const riskCounts = { 'Low Risk': 0, 'Medium Risk': 0, 'High Risk': 0, 'Expired': 0 };
  stats?.data?.batches?.forEach(b => {
      if (b.risk_forecast) riskCounts[b.risk_forecast] = (riskCounts[b.risk_forecast] || 0) + 1;
  });

  return (
    <motion.div 
      className="dashboard-container"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header Section */}
      <motion.div className="dashboard-header-flex" variants={itemVariants}>
        <div className="header-titles">
          <h2>{getGreeting()}, {user?.name ? user.name.split(' ')[0] : 'Hello!'}</h2>
          <p className="header-subtitle">Welcome to your AI Food Freshness command center.</p>
          <div className="header-time" aria-label="Current time">
            <Clock size={14} aria-hidden="true"/> {currentTime.toLocaleDateString()} {currentTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </div>
        </div>
        
        <div className="quick-actions-row" role="group" aria-label="Quick actions">
          <button className="glass-action-btn primary-action" onClick={() => navigate('/scanner')}>
            <Camera size={18} aria-hidden="true"/> Start Scan
          </button>
          <button className="glass-action-btn secondary-action" onClick={() => navigate('/inventory')}>
            <Package size={18} aria-hidden="true"/> Inventory
          </button>
          <button className="glass-action-btn secondary-action" onClick={() => navigate('/reports')}>
            <LineChartIcon size={18} aria-hidden="true"/> Reports
          </button>
          <button className="glass-action-btn secondary-action" onClick={() => navigate('/notifications')}>
            <Bell size={18} aria-hidden="true"/> Alerts
          </button>
        </div>
      </motion.div>

      {/* Primary KPI Cards */}
      <motion.div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }} variants={itemVariants}>
        <KpiCard title="Total Batches" value={totalBatches} icon={Package} iconColor="blue" subtitle="Currently in stock" isPrimary={true}/>
        <KpiCard title="Compliance %" value={compliancePct} icon={ShieldCheck} iconColor={compliancePct > 80 ? "emerald" : "warning"} subtitle="Optimal storage" />
        <KpiCard title="Avg Shelf Life" value={avgDaysRem} icon={Clock} iconColor="emerald" subtitle="Days remaining avg" />
        <KpiCard title="Fresh Items" value={stats?.summary?.freshness?.Fresh || 0} icon={CheckCircle2} iconColor="emerald" subtitle="Excellent condition" />
        <KpiCard title="High Risk Items" value={highRisk} icon={AlertTriangle} iconColor="warning" subtitle="Requires action" />
        <KpiCard title="Spoiled/Expired" value={stats?.summary?.shelf_life?.Expired || 0} icon={Activity} iconColor="danger" subtitle="Past safety thresholds" />
        <KpiCard title="Critical Alerts" value={criticalNotifs} icon={Bell} iconColor="danger" subtitle="Unresolved issues" />
        <KpiCard title="Active Recs." value={Object.keys(stats?.summary?.recommendations || {}).length} icon={Brain} iconColor="blue" subtitle="AI Suggestions" />
      </motion.div>

      {/* Analytics & Activity Grid */}
      <motion.div className="dashboard-grid" variants={itemVariants}>
        
        {/* Charts Column */}
        <div className="charts-column">
            <div className="panel chart-panel" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div>
                    <div className="panel-header">
                        <div>
                        <h3><PieChart size={18} /> Freshness</h3>
                        <p className="panel-subtitle">Status breakdown.</p>
                        </div>
                    </div>
                    <div className="chart-wrapper flex-center">
                        {renderPieChart(stats?.summary?.freshness || {}, "Freshness Distribution")}
                    </div>
                </div>

                <div>
                    <div className="panel-header">
                        <div>
                        <h3><Clock size={18} /> Shelf-Life</h3>
                        <p className="panel-subtitle">Expiry proximity.</p>
                        </div>
                    </div>
                    <div className="chart-wrapper flex-center">
                        {renderPieChart(stats?.summary?.shelf_life || {}, "Shelf-Life Distribution")}
                    </div>
                </div>
            </div>

            <div className="panel chart-panel" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div>
                    <div className="panel-header">
                        <div>
                        <h3><ShieldCheck size={18} /> Storage Compliance</h3>
                        <p className="panel-subtitle">Temperature & Location accuracy.</p>
                        </div>
                    </div>
                    <div className="chart-wrapper flex-center">
                        {renderPieChart(stats?.summary?.storage || {}, "Storage Compliance")}
                    </div>
                </div>

                <div>
                    <div className="panel-header">
                        <div>
                        <h3><AlertTriangle size={18} /> Risk Distribution</h3>
                        <p className="panel-subtitle">AI Spoilage forecast.</p>
                        </div>
                    </div>
                    <div className="chart-wrapper flex-center">
                        {renderPieChart(riskCounts, "Risk Distribution")}
                    </div>
                </div>
            </div>
            
            <div className="panel chart-panel">
                <div className="panel-header">
                    <div>
                    <h3><Bell size={18} /> Notification Severity</h3>
                    <p className="panel-subtitle">Alert distributions.</p>
                    </div>
                </div>
                <div className="chart-wrapper flex-center">
                    {renderPieChart(stats?.summary?.notifications || {}, "Notifications")}
                </div>
            </div>
        </div>

        {/* Side Column: Activity & Status */}
        <div className="side-column">
          
          <div className="panel timeline-panel">
            <div className="panel-header">
              <div>
                <h3><List size={18} /> Recent Activity</h3>
              </div>
            </div>
            <div className="timeline-container">
              {stats?.data?.history?.length > 0 ? stats.data.history.slice(0, 10).map((activity, i) => (
                <div key={i} className="timeline-item">
                  <div className="timeline-marker">
                    <div className="timeline-dot"></div>
                    {i !== Math.min(stats.data.history.length, 10) - 1 && <div className="timeline-line"></div>}
                  </div>
                  <div className="timeline-content glass-card-hover">
                    <div className="timeline-header">
                      <span className="t-time">{new Date(activity.timestamp).toLocaleString([], {month:'short', day:'numeric', hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <p className="t-desc">
                        <strong>{activity.fruit_name}</strong>: {activity.field} changed to {activity.new}.
                    </p>
                  </div>
                </div>
              )) : (
                <div className="empty-state">
                  <List size={32} opacity={0.5} /> 
                  <span>No activity recorded yet.</span>
                </div>
              )}
            </div>
          </div>

        </div>
      </motion.div>
    </motion.div>
  );
}
