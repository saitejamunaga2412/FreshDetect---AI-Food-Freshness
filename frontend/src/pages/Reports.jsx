import React, { useState, useEffect, useMemo } from "react";
import { Activity, Download, FileText, TrendingUp, AlertTriangle, CheckCircle, Clock, Package, Thermometer, MapPin, Zap, Filter } from 'lucide-react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import "./Reports.css";

const API_URL = import.meta.env.VITE_API_URL;
const COLORS = ['var(--accent-primary)', 'var(--warning)', 'var(--danger)', '#3b82f6', '#8b5cf6', '#ec4899'];

export default function Reports() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reportData, setReportData] = useState(null);
  const [lastExportTime, setLastExportTime] = useState(null);
  
  // Filters state
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    category: '',
    storage_location: '',
    risk_level: '',
    freshness_status: ''
  });
  
  // Report Selection State
  const [reportType, setReportType] = useState('Overview'); // Overview, Inventory, Storage, Notifications, History

  const fetchReportData = async () => {
    setLoading(true);
    const token = localStorage.getItem("token");
    if (!token) {
      setError("Please login to view reports.");
      setLoading(false);
      return;
    }

    try {
      // Build query string
      const params = new URLSearchParams();
      Object.keys(filters).forEach(key => {
        if (filters[key]) params.append(key, filters[key]);
      });

      const response = await fetch(`${API_URL}/api/reports/comprehensive?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.status === 401) {
        setError("Session expired. Please login again.");
        setLoading(false);
        return;
      }

      if (!response.ok) throw new Error("Failed to load comprehensive report data.");

      const data = await response.json();
      setReportData(data);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, []); // Run on mount

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };
  
  const applyFilters = () => {
    fetchReportData();
  };

  const clearFilters = () => {
    setFilters({
      start_date: '',
      end_date: '',
      category: '',
      storage_location: '',
      risk_level: '',
      freshness_status: ''
    });
    // Let state update before fetching
    setTimeout(() => {
        const token = localStorage.getItem("token");
        if(token) {
            setLoading(true);
            fetch(`${API_URL}/api/reports/comprehensive`, {
                headers: { Authorization: `Bearer ${token}` }
            }).then(r => r.json()).then(data => {
                setReportData(data);
                setLoading(false);
            }).catch(err => {
                setError(err.message);
                setLoading(false);
            });
        }
    }, 100);
  };

  // Export Handlers
  const handleExportCSV = () => {
    if (!reportData || !reportData.data || !reportData.data.batches) return;
    
    const batches = reportData.data.batches;
    const headers = ["Batch ID", "Fruit Name", "Category", "Quantity", "Freshness Status", "Risk Level", "Days Remaining", "Storage Location", "Compliance", "Recommendations"];
    
    const rows = batches.map(b => [
      `"${b.batch_id}"`,
      `"${b.fruit_name}"`,
      `"${b.category || ''}"`,
      b.quantity,
      b.freshness_status,
      b.risk_forecast,
      b.days_remaining !== null ? b.days_remaining : 'N/A',
      `"${b.storage_location}"`,
      b.storage_compliance,
      `"${b.storage_recommendation} / ${b.consumption_recommendation}"`
    ]);
    
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `FreshDetect_Filtered_Report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setLastExportTime(new Date().toLocaleString());
  };

  const handleExportPDF = () => {
    window.print();
    setLastExportTime(new Date().toLocaleString());
  };

  // UI Helpers
  const renderPieChart = (dataObj, title) => {
    const dataArr = Object.keys(dataObj).map(k => ({ name: k, value: dataObj[k] })).filter(d => d.value > 0);
    if(dataArr.length === 0) return <p className="text-gray-400 text-sm">No data available.</p>;
    
    return (
      <div className="chart-card glass-card">
        <h3>{title}</h3>
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={dataArr}
                innerRadius={50}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {dataArr.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{backgroundColor: 'rgba(17,25,40,0.9)', border: '1px solid var(--border-strong)', borderRadius: '8px', color: 'var(--text-primary)'}}
                itemStyle={{color: 'var(--text-primary)'}}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  if (loading && !reportData) {
    return (
      <div className="reports-container">
        <div className="skeleton-box" style={{height: 150}}></div>
        <div className="skeleton-box" style={{height: 300}}></div>
      </div>
    );
  }

  if (error && !reportData) {
    return (
      <div className="reports-container">
        <div className="reports-error-banner">
          <AlertTriangle size={24}/>
          <strong>{error}</strong>
        </div>
      </div>
    );
  }

  const { summary, data } = reportData || {};

  return (
    <div className="reports-container animate-fade-in">
      <div className="reports-header-block no-print">
        <div>
          <h2>Executive Analytics & Reports</h2>
          <p>Generate comprehensive summaries across all active inventory tracking metrics.</p>
        </div>
      </div>

      {/* FILTER PANEL */}
      <div className="filter-panel glass-card no-print">
        <div className="filter-panel-header">
            <h3><Filter size={18}/> Filters</h3>
        </div>
        <div className="filter-grid">
            <div className="filter-group">
                <label>Category</label>
                <select name="category" value={filters.category} onChange={handleFilterChange}>
                    <option value="">All</option>
                    <option value="Fruit">Fruit</option>
                    <option value="Vegetable">Vegetable</option>
                </select>
            </div>
            <div className="filter-group">
                <label>Risk Level</label>
                <select name="risk_level" value={filters.risk_level} onChange={handleFilterChange}>
                    <option value="">All</option>
                    <option value="Low Risk">Low Risk</option>
                    <option value="Medium Risk">Medium Risk</option>
                    <option value="High Risk">High Risk</option>
                    <option value="Expired">Expired</option>
                </select>
            </div>
            <div className="filter-group">
                <label>Location</label>
                <select name="storage_location" value={filters.storage_location} onChange={handleFilterChange}>
                    <option value="">All</option>
                    <option value="Room Temperature">Room Temp</option>
                    <option value="Refrigerator">Refrigerator</option>
                    <option value="Freezer">Freezer</option>
                </select>
            </div>
            <div className="filter-group">
                <label>Freshness</label>
                <select name="freshness_status" value={filters.freshness_status} onChange={handleFilterChange}>
                    <option value="">All</option>
                    <option value="Fresh">Fresh</option>
                    <option value="Warning">Warning</option>
                    <option value="Spoiled">Spoiled</option>
                </select>
            </div>
            <div className="filter-group" style={{ display: 'flex', alignItems: 'flex-end', gap: '10px' }}>
                <button className="btn btn-primary" onClick={applyFilters}>Apply</button>
                <button className="btn btn-secondary" onClick={clearFilters}>Clear</button>
            </div>
        </div>
      </div>

      {/* REPORT TYPE SELECTOR */}
      <div className="report-tabs no-print" style={{ margin: '20px 0', display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '10px' }}>
        {['Overview', 'Inventory', 'Storage', 'Notifications', 'History'].map(type => (
            <button 
                key={type}
                className={`pill-btn ${reportType === type ? 'active' : ''}`}
                onClick={() => setReportType(type)}
            >{type}</button>
        ))}
      </div>

      {loading && <div style={{textAlign: 'center', padding: '20px', color: 'var(--accent-primary)'}}>Refreshing data...</div>}

      {!loading && reportData && (
        <div className="reports-content">
          
          {/* OVERVIEW TAB */}
          {reportType === 'Overview' && (
              <>
              <div className="exec-summary-grid">
                <div className="exec-card glass-card">
                  <span className="sc-lbl">Total Batches</span>
                  <span className="sc-val">{summary.inventory.total_items}</span>
                </div>
                <div className="exec-card glass-card border-green">
                  <span className="sc-lbl">Fresh Batches</span>
                  <span className="sc-val text-green">{summary.freshness.Fresh}</span>
                </div>
                <div className="exec-card glass-card border-yellow">
                  <span className="sc-lbl">Near Expiry</span>
                  <span className="sc-val text-yellow">{summary.shelf_life.Near_Expiry}</span>
                </div>
                <div className="exec-card glass-card border-red">
                  <span className="sc-lbl">Non-Compliant</span>
                  <span className="sc-val text-red">{summary.storage['Non-Compliant'] || 0}</span>
                </div>
              </div>

              <div className="insights-charts-row">
                  {renderPieChart(summary.freshness, "Freshness Distribution")}
                  {renderPieChart(summary.shelf_life, "Shelf-Life Distribution")}
                  {renderPieChart(summary.storage, "Storage Compliance")}
              </div>
              </>
          )}

          {/* INVENTORY TAB */}
          {reportType === 'Inventory' && (
              <div className="glass-card" style={{ padding: '20px' }}>
                  <h3 style={{marginBottom: '15px'}}>Inventory Data (Filtered)</h3>
                  <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                          <thead>
                              <tr style={{ borderBottom: '1px solid var(--border-strong)' }}>
                                  <th style={{padding: '10px'}}>Batch ID</th>
                                  <th style={{padding: '10px'}}>Fruit</th>
                                  <th style={{padding: '10px'}}>Risk</th>
                                  <th style={{padding: '10px'}}>Days Rem.</th>
                                  <th style={{padding: '10px'}}>Storage Rec.</th>
                              </tr>
                          </thead>
                          <tbody>
                              {data.batches.length === 0 ? (
                                  <tr><td colSpan="5" style={{padding: '10px', textAlign: 'center'}}>No batches match filters.</td></tr>
                              ) : data.batches.map(b => (
                                  <tr key={b._id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                      <td style={{padding: '10px', color: '#60a5fa'}}>{b.batch_id}</td>
                                      <td style={{padding: '10px'}}>{b.fruit_name}</td>
                                      <td style={{padding: '10px'}}>{b.risk_forecast}</td>
                                      <td style={{padding: '10px'}}>{b.days_remaining}</td>
                                      <td style={{padding: '10px'}}>{b.storage_recommendation}</td>
                                  </tr>
                              ))}
                          </tbody>
                      </table>
                  </div>
              </div>
          )}

          {/* HISTORY TAB */}
          {reportType === 'History' && (
              <div className="glass-card" style={{ padding: '20px' }}>
                  <h3 style={{marginBottom: '15px'}}>Batch History Audit Log (Filtered)</h3>
                  <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                          <thead>
                              <tr style={{ borderBottom: '1px solid var(--border-strong)' }}>
                                  <th style={{padding: '8px'}}>Time</th>
                                  <th style={{padding: '8px'}}>Batch</th>
                                  <th style={{padding: '8px'}}>Field</th>
                                  <th style={{padding: '8px'}}>Change</th>
                              </tr>
                          </thead>
                          <tbody>
                              {data.history.length === 0 ? (
                                  <tr><td colSpan="4" style={{padding: '10px', textAlign: 'center'}}>No history available.</td></tr>
                              ) : data.history.map((h, i) => (
                                  <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                      <td style={{padding: '8px', color: 'var(--text-secondary)'}}>{new Date(h.timestamp).toLocaleString()}</td>
                                      <td style={{padding: '8px'}}>{h.batch_id} ({h.fruit_name})</td>
                                      <td style={{padding: '8px'}}>{h.field}</td>
                                      <td style={{padding: '8px'}}>{h.previous} &rarr; {h.new}</td>
                                  </tr>
                              ))}
                          </tbody>
                      </table>
                  </div>
              </div>
          )}

          {/* OTHER TABS (Storage, Notifications) Placeholder text for brevity in this rewrite, they share the same charts */}
          {(reportType === 'Storage' || reportType === 'Notifications') && (
              <div className="glass-card" style={{ padding: '20px' }}>
                  <h3>{reportType} Details</h3>
                  <div className="insights-charts-row" style={{ marginTop: '20px' }}>
                      {reportType === 'Storage' && renderPieChart(summary.storage, "Storage Compliance")}
                      {reportType === 'Notifications' && renderPieChart(summary.notifications, "Notifications by Severity")}
                  </div>
              </div>
          )}

          {/* 6. Export Center */}
          <motion.div className="export-center glass-card no-print" style={{marginTop: '30px'}}>
            <div className="export-info">
              <h3><Download size={18}/> Export Center</h3>
              <p>Download your filtered executive report for offline review.</p>
              {lastExportTime && <span className="export-time"><Clock size={12}/> Last exported: {lastExportTime}</span>}
            </div>
            <div className="export-actions">
              <button className="btn btn-secondary" onClick={handleExportCSV}>
                <FileText size={16}/> Export CSV
              </button>
              <button className="btn btn-primary" onClick={handleExportPDF}>
                <FileText size={16}/> Export PDF
              </button>
            </div>
          </motion.div>

        </div>
      )}
    </div>
  );
}
