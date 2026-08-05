import React, { useState, useEffect } from 'react';
import { Palette, Bell, Info, Server, Database, Brain, ArrowRight, LogOut, Code, User, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import './Settings.css';

const API_URL = import.meta.env.VITE_API_URL;

export default function Settings() {
  const navigate = useNavigate();
  
  // Local state for interactive settings
  const [prefs, setPrefs] = useState(() => {
    const saved = localStorage.getItem('freshdetect_settings');
    return saved ? JSON.parse(saved) : {
      theme: 'Emerald Glass',
      emailNotifs: true,
      browserNotifs: false
    };
  });

  const [healthStatus, setHealthStatus] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);

  // Sync to localStorage
  useEffect(() => {
    localStorage.setItem('freshdetect_settings', JSON.stringify(prefs));
  }, [prefs]);

  // Apply Theme
  useEffect(() => {
    if (prefs.theme === 'Dark') {
      document.documentElement.classList.add('dark-theme');
      document.documentElement.classList.remove('light-theme');
    } else if (prefs.theme === 'Light') {
      document.documentElement.classList.add('light-theme');
      document.documentElement.classList.remove('dark-theme');
    } else {
      document.documentElement.classList.remove('dark-theme', 'light-theme');
    }
  }, [prefs.theme]);

  // Fetch Health Status
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/api/health`);
        if (response.ok) {
          const data = await response.json();
          setHealthStatus(data);
        }
      } catch (err) {
        setHealthStatus({ fastapi: "Offline", mongodb: "Offline", yolo: "Unknown", ml_model: "Unknown", foodkeeper: "Unknown" });
      } finally {
        setLoadingHealth(false);
      }
    };
    fetchHealth();
  }, []);

  const updatePref = (key, value) => {
    setPrefs(prev => ({ ...prev, [key]: value }));
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    toast.success("Logged out successfully");
    navigate('/login');
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  const StatusIndicator = ({ status }) => {
    if (status === 'Online' || status === 'Connected' || status === 'Loaded') {
      return <span className="status-badge-small success"><CheckCircle2 size={12}/> {status}</span>;
    }
    if (status === 'Offline' || status === 'Disconnected') {
      return <span className="status-badge-small danger"><AlertCircle size={12}/> {status}</span>;
    }
    return <span className="status-badge-small warning">{status || "Unknown"}</span>;
  };

  return (
    <div className="settings-wrapper animate-fade-in">
      <div className="settings-header-block">
        <div>
          <h2>Application Settings</h2>
          <p>Configure FreshDetect AI preferences and monitor system health.</p>
        </div>
      </div>

      <motion.div 
        className="settings-layout"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {/* 1. Appearance */}
        <motion.div className="settings-section" variants={itemVariants}>
          <h3><Palette size={18}/> Appearance</h3>
          <div className="settings-list glass-card">
            <div className="setting-item">
              <div className="setting-info">
                <h4>Interface Theme</h4>
                <p>Customize the workspace aesthetic.</p>
              </div>
              <select className="glass-select" value={prefs.theme} onChange={e => updatePref('theme', e.target.value)}>
                <option>Emerald Glass (Default)</option>
                <option>Dark</option>
                <option>Light</option>
              </select>
            </div>
          </div>
        </motion.div>

        {/* 2. Notification Preferences */}
        <motion.div className="settings-section" variants={itemVariants}>
          <h3><Bell size={18}/> Notification Preferences</h3>
          <div className="settings-list glass-card">
            <div className="setting-item">
              <div className="setting-info">
                <h4>Browser Notifications</h4>
                <p>Receive push notifications for inventory alerts.</p>
              </div>
              <label className="glass-toggle">
                <input type="checkbox" className="sr-only" checked={prefs.browserNotifs} onChange={e => updatePref('browserNotifs', e.target.checked)}/>
                <div className={`toggle-track ${prefs.browserNotifs ? 'active' : ''}`}><div className="toggle-thumb"></div></div>
              </label>
            </div>
            <div className="setting-item">
              <div className="setting-info">
                <h4>Email Notifications</h4>
                <p>Receive weekly inventory digests via email.</p>
              </div>
              <label className="glass-toggle">
                <input type="checkbox" className="sr-only" checked={prefs.emailNotifs} onChange={e => updatePref('emailNotifs', e.target.checked)}/>
                <div className={`toggle-track ${prefs.emailNotifs ? 'active' : ''}`}><div className="toggle-thumb"></div></div>
              </label>
            </div>
          </div>
        </motion.div>

        {/* 3. Account Shortcuts */}
        <motion.div className="settings-section" variants={itemVariants}>
          <h3><User size={18}/> Account</h3>
          <div className="settings-list glass-card">
            <div className="setting-item" style={{ cursor: 'pointer' }} onClick={() => navigate('/profile')}>
              <div className="setting-info">
                <h4>Edit Profile</h4>
                <p>Update your name, location, and avatar.</p>
              </div>
              <ArrowRight size={18} className="text-secondary" />
            </div>
            <div className="setting-item" style={{ cursor: 'pointer', borderTop: '1px solid var(--border-subtle)' }} onClick={handleLogout}>
              <div className="setting-info">
                <h4 style={{ color: 'var(--danger)' }}>Logout</h4>
                <p>Securely sign out of your account.</p>
              </div>
              <LogOut size={18} color="var(--danger)" />
            </div>
          </div>
        </motion.div>

        {/* 4. About & System Health */}
        <motion.div className="settings-section" variants={itemVariants}>
          <h3><Info size={18}/> About FreshDetect AI</h3>
          <div className="settings-list glass-card" style={{ padding: '20px' }}>
            
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ fontSize: '1.1rem', marginBottom: '4px' }}>FreshDetect AI Platform</h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Version 1.0.0-beta</p>
            </div>

            <div className="health-grid">
              {loadingHealth ? (
                <div className="skeleton-box" style={{height: 100, width: '100%', borderRadius: 8}}></div>
              ) : (
                <>
                  <div className="health-row">
                    <div className="health-label"><Server size={16}/> FastAPI Server</div>
                    <StatusIndicator status={healthStatus?.fastapi} />
                  </div>
                  <div className="health-row">
                    <div className="health-label"><Database size={16}/> MongoDB</div>
                    <StatusIndicator status={healthStatus?.mongodb} />
                  </div>
                  <div className="health-row">
                    <div className="health-label"><Brain size={16}/> YOLO Vision Model</div>
                    <StatusIndicator status={healthStatus?.yolo} />
                  </div>
                  <div className="health-row">
                    <div className="health-label"><Code size={16}/> Freshness ML Model</div>
                    <StatusIndicator status={healthStatus?.ml_model} />
                  </div>
                  <div className="health-row">
                    <div className="health-label"><Database size={16}/> FoodKeeper Dataset</div>
                    <StatusIndicator status={healthStatus?.foodkeeper} />
                  </div>
                </>
              )}
            </div>

          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
