import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Search, Filter, Trash2, Calendar, Eye, Download, ChevronRight, X, Clock, Target, Activity, ShieldAlert, Package, Thermometer, Droplets, MapPin, Inbox, Box } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import './ScanHistory.css';

const API_URL = import.meta.env.VITE_API_URL;

// Reusable Details Modal Component
const DetailsModal = ({ scan, onClose }) => {
  if (!scan) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <motion.div 
        className="modal-content glass-card"
        onClick={e => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <button className="modal-close" onClick={onClose} aria-label="Close modal"><X size={20}/></button>
        
        <div className="modal-layout">
          <div className="modal-image-col">
            <img src={scan.image_url.startsWith('http') ? scan.image_url : `${API_URL}${scan.image_url}`} alt={scan.fruit || 'Scan image'} className="modal-img" />
            <div className="modal-details">
              <h2 id="modal-title">{scan.fruit || 'Unknown Item'}</h2>
              <span className="modal-subtitle">Produce</span>
            </div>
            
            <div className="modal-metrics-grid">
              <div className="m-metric">
                <span className="m-label"><Target size={14}/> Detection Confidence</span>
                <span className="m-val">{scan.detection_confidence ? (scan.detection_confidence * 100).toFixed(1) + '%' : 'N/A'}</span>
              </div>
              <div className="m-metric">
                <span className="m-label"><Activity size={14}/> Freshness</span>
                {(scan.overall_score ?? scan.quality_score) !== null && (scan.overall_score ?? scan.quality_score) !== undefined ? (
                  <span className="m-val" style={{color: (scan.overall_score ?? scan.quality_score) >= 75 ? 'var(--accent-primary)' : (scan.overall_score ?? scan.quality_score) >= 40 ? 'var(--warning)' : 'var(--danger)'}}>
                    {scan.overall_score ?? scan.quality_score}%
                  </span>
                ) : (
                  <span className="m-val pending-text">Pending AI Model</span>
                )}
              </div>
              <div className="m-metric">
                <span className="m-label"><Clock size={14}/> Recommended Storage Duration</span>
                {scan.shelf_life ? (
                  <span className="m-val" style={{textTransform: 'capitalize'}}>{typeof scan.shelf_life === 'object' ? Object.entries(scan.shelf_life).map(([k,v]) => `${k}: ${v}`).join(' | ') : scan.shelf_life}</span>
                ) : (
                  <span className="m-val pending-text">Not Available</span>
                )}
              </div>
            </div>

            <div className="modal-section">
              <h3><Package size={16}/> Storage Recommendation</h3>
              <p className="modal-desc">{scan.storage_instructions || 'Not Available.'}</p>
            </div>

            <div className="modal-section">
              <h3><ShieldAlert size={16}/> Spoilage Reason</h3>
              <p className="modal-desc">{scan.spoilage_reason && scan.spoilage_reason !== "None" ? scan.spoilage_reason : 'No spoilage detected.'}</p>
            </div>

          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default function ScanHistory() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortType, setSortType] = useState('Newest');
  const [selectedScan, setSelectedScan] = useState(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/scan-history?limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setScans(response.data.scans || []);
    } catch (err) {
      console.error("Failed to load scan history:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this scan record?")) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/scan-history/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setScans(scans.filter(s => s._id !== id));
    } catch (err) {
      alert("Failed to delete scan.");
    }
  };

  const filteredAndSortedScans = useMemo(() => {
    let result = scans.filter(scan => {
      const categoryText = scan.freshness_category || scan.freshness_prediction || '';
      const matchesSearch = (scan.fruit || '').toLowerCase().includes(searchTerm.toLowerCase()) || 
                            categoryText.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesSearch;
    });

    result.sort((a, b) => {
      const scoreA = a.overall_score ?? a.quality_score ?? 0;
      const scoreB = b.overall_score ?? b.quality_score ?? 0;
      if (sortType === 'Newest') return new Date(b.created_at) - new Date(a.created_at);
      if (sortType === 'Oldest') return new Date(a.created_at) - new Date(b.created_at);
      if (sortType === 'Highest Freshness') return scoreB - scoreA;
      if (sortType === 'Lowest Freshness') return scoreA - scoreB;
      return 0;
    });

    return result;
  }, [scans, searchTerm, sortType]);

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } },
    exit: { opacity: 0, scale: 0.95, transition: { duration: 0.2 } }
  };

  const getBadgeColor = (category) => {
    const lower = (category || '').toLowerCase();
    if (lower.includes('fresh')) return 'badge-fresh';
    if (lower.includes('spoil') || lower.includes('rotten')) return 'badge-spoiled';
    return 'badge-warning';
  };

  return (
    <div className="history-container animate-fade-in">
      <div className="history-header-block">
        <div>
          <h2>AI Analysis Journal</h2>
          <p>Review your past food freshness scans and AI insights.</p>
        </div>
      </div>

      <div className="history-controls">
        <div className="search-box">
          <Search className="search-icon" size={18} />
          <input 
            type="text" 
            placeholder="Search by fruit name..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search history"
          />
        </div>

        <div className="filters-wrapper">
          <select 
            className="glass-sort" 
            value={sortType} 
            onChange={(e) => setSortType(e.target.value)}
            aria-label="Sort scans"
          >
            <option value="Newest">Newest First</option>
            <option value="Oldest">Oldest First</option>
            <option value="Highest Freshness">Highest Freshness</option>
            <option value="Lowest Freshness">Lowest Freshness</option>
          </select>
        </div>
      </div>

      <div className="history-grid">
        {loading ? (
          Array.from({length: 4}).map((_, i) => (
            <div key={i} className="skeleton-card"></div>
          ))
        ) : filteredAndSortedScans.length === 0 ? (
          <div className="history-empty">
            <Inbox size={48} opacity={0.3} className="empty-icon"/>
            <h3>No scans yet</h3>
            <p>Start your first AI freshness scan to build your journal.</p>
            <button className="btn btn-primary mt-4" onClick={() => navigate('/scanner')}>
              Go to Scanner
            </button>
          </div>
        ) : (
          <motion.div 
            className="history-list-animated"
            variants={containerVariants}
            initial="hidden"
            animate="show"
          >
            <AnimatePresence>
              {filteredAndSortedScans.map(scan => (
                <motion.div 
                  key={scan._id} 
                  className="journal-card glass-card"
                  variants={itemVariants}
                  exit="exit"
                  layout
                >
                  <div className="jc-image">
                    <img src={scan.image_url.startsWith('http') ? scan.image_url : `${API_URL}${scan.image_url}`} alt={scan.fruit || 'Food image'} />
                    <span className={`status-badge ${getBadgeColor(scan.freshness_category || scan.freshness_prediction)}`}>
                      {scan.freshness_category || scan.freshness_prediction || 'Pending AI Model'}
                    </span>
                  </div>
                  
                  <div className="jc-content">
                    <div className="jc-header">
                      <div>
                        <h3>{scan.fruit || 'Unknown Item'}</h3>
                        <span className="jc-category">Produce</span>
                      </div>
                      <div className="jc-time">
                        <Calendar size={12}/> 
                        {new Date(scan.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    
                    <div className="jc-metrics">
                      <div className="jc-metric">
                        <span className="lbl">Freshness</span>
                        {(scan.overall_score ?? scan.quality_score) !== null && (scan.overall_score ?? scan.quality_score) !== undefined ? (
                          <span className="val" style={{color: (scan.overall_score ?? scan.quality_score) >= 75 ? 'var(--accent-primary)' : (scan.overall_score ?? scan.quality_score) >= 40 ? 'var(--warning)' : 'var(--danger)'}}>
                            {scan.overall_score ?? scan.quality_score}%
                          </span>
                        ) : (
                          <span className="val pending-sm">Pending Model</span>
                        )}
                      </div>
                      <div className="jc-metric">
                        <span className="lbl">Rec. Storage</span>
                        {scan.shelf_life ? (
                          <span className="val" style={{textTransform: 'capitalize'}}>{typeof scan.shelf_life === 'object' ? Object.entries(scan.shelf_life).map(([k,v]) => `${k}: ${v}`).join(' | ') : scan.shelf_life}</span>
                        ) : (
                          <span className="val pending-sm">Not Available</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="jc-footer">
                      <div className="jc-actions">
                        <button className="icon-btn tooltip-parent" onClick={() => setSelectedScan(scan)} aria-label="View Details">
                          <Eye size={16} />
                          <span className="tooltip">Details</span>
                        </button>
                        <button className="icon-btn danger tooltip-parent" onClick={(e) => handleDelete(scan._id, e)} aria-label="Delete Scan">
                          <Trash2 size={16} />
                          <span className="tooltip">Delete</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>

      <AnimatePresence>
        {selectedScan && (
          <DetailsModal scan={selectedScan} onClose={() => setSelectedScan(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
