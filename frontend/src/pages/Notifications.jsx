import React, { useState, useEffect, useMemo } from "react";
import { Bell, AlertTriangle, AlertCircle, Info, CheckCircle, Package, Search, Filter, Check, Trash2, Eye, MapPin } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from 'react-router-dom';
import "./Notifications.css";

const API_URL = import.meta.env.VITE_API_URL;

export default function Notifications() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notifications, setNotifications] = useState([]);
  
  // Local state for actions
  const [readNotifs, setReadNotifs] = useState(new Set());
  const [deletedNotifs, setDeletedNotifs] = useState(new Set());
  
  // Filtering
  const [filterType, setFilterType] = useState('All');

  const navigate = useNavigate();

  // Load state from localStorage on mount
  useEffect(() => {
    const savedRead = localStorage.getItem('freshdetect_read_notifs');
    const savedDeleted = localStorage.getItem('freshdetect_deleted_notifs');
    if (savedRead) setReadNotifs(new Set(JSON.parse(savedRead)));
    if (savedDeleted) setDeletedNotifs(new Set(JSON.parse(savedDeleted)));
  }, []);

  // Sync state to localStorage
  useEffect(() => {
    localStorage.setItem('freshdetect_read_notifs', JSON.stringify(Array.from(readNotifs)));
    localStorage.setItem('freshdetect_deleted_notifs', JSON.stringify(Array.from(deletedNotifs)));
  }, [readNotifs, deletedNotifs]);

  useEffect(() => {
    const fetchNotifications = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Please login to view notifications.");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/notifications`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.status === 401) {
          setError("Session expired. Please login again.");
          setLoading(false);
          return;
        }

        if (!response.ok) throw new Error("Failed to load notifications.");

        const data = await response.json();
        setNotifications(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchNotifications();
  }, []);

  // Actions
  const handleMarkRead = (id, e) => {
    e.stopPropagation();
    const newRead = new Set(readNotifs);
    newRead.add(id);
    setReadNotifs(newRead);
  };

  const handleDelete = (id, e) => {
    e.stopPropagation();
    const newDeleted = new Set(deletedNotifs);
    newDeleted.add(id);
    setDeletedNotifs(newDeleted);
  };

  const handleActionClick = (alert) => {
    navigate('/inventory');
  };

  // Filtered Alerts
  const filteredAlerts = useMemo(() => {
    return notifications
      .filter(alert => !deletedNotifs.has(alert.id))
      .filter(alert => {
        const isRead = readNotifs.has(alert.id);
        if (filterType === 'Unread') return !isRead;
        if (filterType === 'Read') return isRead;
        
        // Group by severity
        if (['CRITICAL', 'WARNING', 'INFO'].includes(filterType)) return alert.severity === filterType;
        
        return true;
      });
  }, [notifications, filterType, readNotifs, deletedNotifs]);

  // Metrics
  const summary = useMemo(() => {
    const unread = notifications.filter(a => !deletedNotifs.has(a.id) && !readNotifs.has(a.id)).length;
    const critical = notifications.filter(a => !deletedNotifs.has(a.id) && a.severity === 'CRITICAL').length;
    const warning = notifications.filter(a => !deletedNotifs.has(a.id) && a.severity === 'WARNING').length;
    const info = notifications.filter(a => !deletedNotifs.has(a.id) && a.severity === 'INFO').length;
    const total = notifications.filter(a => !deletedNotifs.has(a.id)).length;
    return { total, unread, critical, warning, info };
  }, [notifications, readNotifs, deletedNotifs]);

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0, transition: { type: "spring", stiffness: 300, damping: 24 } },
    exit: { opacity: 0, scale: 0.95, transition: { duration: 0.2 } }
  };

  const getIcon = (severity) => {
    switch(severity) {
      case 'CRITICAL': return <AlertCircle size={20} />;
      case 'WARNING': return <AlertTriangle size={20} />;
      case 'INFO': return <Info size={20} />;
      default: return <Bell size={20} />;
    }
  };
  
  const getSeverityClass = (severity) => {
      if (severity === 'CRITICAL') return 'type-critical';
      if (severity === 'WARNING') return 'type-warning';
      return 'type-information';
  };

  if (loading) {
    return (
      <div className="notif-container">
        <div className="skeleton-box" style={{height: 120}}></div>
        <div className="skeleton-box" style={{height: 400}}></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="notif-container">
        <div className="notif-error-banner">
          <AlertTriangle size={24}/>
          <strong>{error}</strong>
        </div>
      </div>
    );
  }

  return (
    <div className="notif-container animate-fade-in">
      <div className="notif-header-block">
        <div>
          <h2>AI Alert Center</h2>
          <p>Real-time notifications and recommended actions for your inventory.</p>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="notif-summary-grid">
        <div className="summary-card glass-card">
          <span className="sc-lbl">Total Alerts</span>
          <span className="sc-val">{summary.total}</span>
        </div>
        <div className="summary-card glass-card border-red">
          <span className="sc-lbl">Critical</span>
          <span className="sc-val text-red">{summary.critical}</span>
        </div>
        <div className="summary-card glass-card border-yellow">
          <span className="sc-lbl">Warnings</span>
          <span className="sc-val text-yellow">{summary.warning}</span>
        </div>
        <div className="summary-card glass-card border-blue">
          <span className="sc-lbl">Information</span>
          <span className="sc-val text-blue">{summary.info}</span>
        </div>
        <div className="summary-card glass-card">
          <span className="sc-lbl">Unread</span>
          <span className="sc-val">{summary.unread}</span>
        </div>
      </div>

      <div className="notif-layout">
        <div className="notif-main-col" style={{ width: '100%' }}>
          {/* Filters */}
          <div className="notif-filters-wrapper glass-card">
            <Filter size={16} color="var(--text-secondary)"/>
            <div className="pill-filters" role="group" aria-label="Filter notifications">
              {['All', 'CRITICAL', 'WARNING', 'INFO', 'Unread', 'Read'].map(f => {
                return (
                  <button 
                    key={f}
                    className={`pill-btn ${filterType === f ? 'active' : ''}`}
                    onClick={() => setFilterType(f)}
                    aria-pressed={filterType === f}
                  >
                    {f}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Timeline / Alert Cards */}
          <div className="notif-timeline" aria-live="polite">
            {filteredAlerts.length === 0 ? (
              <div className="notif-empty">
                <Bell size={48} opacity={0.3} className="empty-icon"/>
                <h3>No alerts found.</h3>
                <p>You're all caught up!</p>
              </div>
            ) : (
              <motion.div 
                className="notif-list"
                variants={containerVariants}
                initial="hidden"
                animate="show"
              >
                <AnimatePresence>
                  {filteredAlerts.map(alert => {
                    const isRead = readNotifs.has(alert.id);
                    return (
                      <motion.div 
                        key={alert.id}
                        variants={itemVariants}
                        exit="exit"
                        layout
                        className={`notif-card glass-card ${getSeverityClass(alert.severity)} ${isRead ? 'is-read' : ''}`}
                      >
                        <div className="notif-icon-wrap">
                          {getIcon(alert.severity)}
                        </div>
                        <div className="notif-content">
                          <div className="notif-head">
                            <h3>{alert.title}</h3>
                            <span className="notif-time">{new Date(alert.timestamp).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}</span>
                          </div>
                          <p>{alert.message}</p>
                          
                          <div className="notif-footer" style={{ flexWrap: 'wrap' }}>
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                <span className={`notif-badge badge-${alert.type.toLowerCase().replace(/\s+/g, '-')}`}>{alert.type}</span>
                                {alert.related_batch && (
                                    <span className="notif-badge" style={{background: 'var(--border-strong)'}}>Batch: {alert.related_batch}</span>
                                )}
                                {alert.recommendation && (
                                    <span className="notif-badge badge-success" style={{background: 'rgba(16, 185, 129, 0.1)', color: 'var(--accent-primary)', border: '1px solid rgba(16, 185, 129, 0.2)'}}>Recommends: {alert.recommendation}</span>
                                )}
                            </div>
                            <div className="notif-actions">
                              <button className="btn btn-secondary btn-sm" onClick={() => handleActionClick(alert)}>
                                View Details
                              </button>
                              {!isRead && (
                                <button className="icon-btn tooltip-parent text-emerald" onClick={(e) => handleMarkRead(alert.id, e)} aria-label="Mark as Read">
                                  <Check size={16}/>
                                  <span className="tooltip">Mark Read</span>
                                </button>
                              )}
                              <button className="icon-btn danger tooltip-parent" onClick={(e) => handleDelete(alert.id, e)} aria-label="Delete">
                                <Trash2 size={16}/>
                                <span className="tooltip">Delete</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )
                  })}
                </AnimatePresence>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
