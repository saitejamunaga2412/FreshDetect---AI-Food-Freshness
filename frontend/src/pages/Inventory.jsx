import React, { useState, useEffect } from "react";
import { Search, Trash2, Edit3, X, Package, Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import { useOutletContext } from 'react-router-dom';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import "./Inventory.css";

const API_URL = import.meta.env.VITE_API_URL;

const AddBatchModal = ({ onClose, onSave, isSubmitting }) => {
  const [formData, setFormData] = useState({
    batch_id: '',
    fruit_name: '',
    category: 'Fruit',
    quantity: 1,
    storage_location: 'Room Temperature',
    temperature: '',
    humidity: '',
    supplier: ''
  });

  const handleChange = (e) => setFormData({...formData, [e.target.name]: e.target.value});

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <motion.div className="edit-modal glass-card" onClick={e => e.stopPropagation()} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}>
        <button className="modal-close" onClick={onClose}><X size={20}/></button>
        <h2>Add Inventory Batch</h2>
        <form onSubmit={handleSubmit} className="edit-form">
          <div className="form-group">
            <label>Batch ID</label>
            <input type="text" name="batch_id" value={formData.batch_id} onChange={handleChange} required className="form-input" />
          </div>
          <div className="form-group">
            <label>Produce Name</label>
            <input type="text" name="fruit_name" value={formData.fruit_name} onChange={handleChange} required className="form-input" />
          </div>
          <div className="form-group">
            <label>Category</label>
            <select name="category" value={formData.category} onChange={handleChange} required className="form-input">
              <option value="Fruit">Fruit</option>
              <option value="Vegetable">Vegetable</option>
            </select>
          </div>
          <div className="form-group">
            <label>Storage Location</label>
            <select name="storage_location" value={formData.storage_location} onChange={handleChange} required className="form-input">
              <option value="Room Temperature">Room Temperature</option>
              <option value="Refrigerator">Refrigerator</option>
              <option value="Freezer">Freezer</option>
            </select>
          </div>
          <div className="form-group">
            <label>Quantity</label>
            <input type="number" name="quantity" min="1" value={formData.quantity} onChange={handleChange} required className="form-input" />
          </div>
          <div className="form-group" style={{ display: 'flex', gap: '16px' }}>
            <div style={{ flex: 1 }}>
              <label>Temperature (°C)</label>
              <input type="number" step="0.1" name="temperature" value={formData.temperature} onChange={handleChange} className="form-input" />
            </div>
            <div style={{ flex: 1 }}>
              <label>Humidity (%)</label>
              <input type="number" step="0.1" name="humidity" value={formData.humidity} onChange={handleChange} className="form-input" />
            </div>
          </div>
          <div className="form-group">
            <label>Supplier (Optional)</label>
            <input type="text" name="supplier" value={formData.supplier} onChange={handleChange} className="form-input" />
          </div>
          <button type="submit" className="btn btn-primary mt-4" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Add Batch'}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

const EditBatchModal = ({ batch, onClose, onSave, isSubmitting }) => {
  const [formData, setFormData] = useState({
    quantity: batch.quantity,
    storage_location: batch.storage_location || 'Room Temperature',
    temperature: batch.temperature || '',
    humidity: batch.humidity || ''
  });

  const handleChange = (e) => setFormData({...formData, [e.target.name]: e.target.value});

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(batch._id, formData);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <motion.div className="edit-modal glass-card" onClick={e => e.stopPropagation()} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}>
        <button className="modal-close" onClick={onClose}><X size={20}/></button>
        <h2>Edit Batch Quantity</h2>
        <form onSubmit={handleSubmit} className="edit-form">
          <div className="form-group">
            <label>Storage Location</label>
            <select name="storage_location" value={formData.storage_location} onChange={handleChange} required className="form-input">
              <option value="Room Temperature">Room Temperature</option>
              <option value="Refrigerator">Refrigerator</option>
              <option value="Freezer">Freezer</option>
            </select>
          </div>
          <div className="form-group">
            <label>Quantity</label>
            <input type="number" name="quantity" min="1" value={formData.quantity} onChange={handleChange} required className="form-input" />
          </div>
          <button type="submit" className="btn btn-primary mt-4" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

const Inventory = () => {
  const { userProfile } = useOutletContext() || {};
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("Active");
  const [skip, setSkip] = useState(0);
  const limit = 20;

  const [showAddModal, setShowAddModal] = useState(false);
  const [editingBatch, setEditingBatch] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchBatches();
    fetchStats();
  }, [skip, filterType]);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_URL}/api/inventory/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to fetch stats", err);
    }
  };

  const fetchBatches = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const status = filterType === 'Archived' ? 'archived' : 'active';
      const res = await fetch(`${API_URL}/api/inventory/batches?skip=${skip}&limit=${limit}&status=${status}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to fetch batches");
      const data = await res.json();
      setBatches(data);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSave = async (formData) => {
    setIsSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      const payload = { ...formData, quantity: parseInt(formData.quantity) };
      if (payload.temperature) payload.temperature = parseFloat(payload.temperature);
      else delete payload.temperature;
      if (payload.humidity) payload.humidity = parseFloat(payload.humidity);
      else delete payload.humidity;
      
      const res = await fetch(`${API_URL}/api/inventory/batches`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to add batch");
      toast.success("Batch added successfully");
      setShowAddModal(false);
      fetchBatches();
      fetchStats();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSave = async (id, data) => {
    setIsSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      const payload = { 
        quantity: parseInt(data.quantity),
        storage_location: data.storage_location 
      };
      if (data.temperature) payload.temperature = parseFloat(data.temperature);
      if (data.humidity) payload.humidity = parseFloat(data.humidity);
      
      const res = await fetch(`${API_URL}/api/inventory/batches/${id}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to update batch");
      toast.success("Batch updated successfully");
      setEditingBatch(null);
      fetchBatches();
      fetchStats();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this batch?")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_URL}/api/inventory/batches/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to delete batch");
      toast.success("Batch deleted (archived) successfully");
      fetchBatches();
      fetchStats();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const filteredBatches = batches.filter(b => 
    b.fruit_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.batch_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ margin: '0 0 8px 0' }}>Inventory Batches</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Manage your produce stock and expiry dates.</p>
        </div>
        {['Retail Manager', 'Warehouse Operator', 'Administrator', 'Admin', 'Retailer'].includes(userProfile?.role) && (
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Plus size={18} /> Add Batch
          </button>
        )}
      </div>

      {stats && filterType === 'Active' && (
        <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <div className="glass-card stat-card" style={{ padding: '16px', textAlign: 'center' }}>
            <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-secondary)' }}>Total Items</h4>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{stats.total_items}</span>
          </div>
          <div className="glass-card stat-card" style={{ padding: '16px', textAlign: 'center' }}>
            <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-secondary)' }}>Fruits / Veg</h4>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{stats.fruits_count} / {stats.vegetables_count}</span>
          </div>
          <div className="glass-card stat-card" style={{ padding: '16px', textAlign: 'center' }}>
            <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-secondary)' }}>Near Expiry</h4>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: stats.near_expiry_count > 0 ? 'var(--warning)' : 'var(--accent-primary)' }}>{stats.near_expiry_count}</span>
          </div>
          <div className="glass-card stat-card" style={{ padding: '16px', textAlign: 'center' }}>
            <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-secondary)' }}>Low Stock Batches</h4>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: stats.low_stock_count > 0 ? 'var(--danger)' : 'var(--accent-primary)' }}>{stats.low_stock_count}</span>
          </div>
          <div className="glass-card stat-card" style={{ padding: '16px', textAlign: 'center', borderColor: stats.healthy_percentage > 80 ? 'var(--accent-primary)' : 'var(--warning)', borderWidth: '1px', borderStyle: 'solid' }}>
            <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-secondary)' }}>Inv. Health</h4>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: stats.healthy_percentage > 80 ? 'var(--accent-primary)' : 'var(--warning)' }}>{stats.healthy_percentage}%</span>
          </div>
        </div>
      )}

      <div className="history-controls glass-card" style={{ padding: '16px', marginBottom: '24px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
        <div className="search-box" style={{ flex: 1, minWidth: '300px' }}>
          <Search className="search-icon" size={18} />
          <input 
            type="text" 
            placeholder="Search by name or batch ID..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="pill-filters">
          <button className={`pill-btn ${filterType === 'Active' ? 'active' : ''}`} onClick={() => {setFilterType('Active'); setSkip(0);}}>Active</button>
          <button className={`pill-btn ${filterType === 'Archived' ? 'active' : ''}`} onClick={() => {setFilterType('Archived'); setSkip(0);}}>Archived</button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--accent-primary)' }}>Loading batches...</div>
      ) : filteredBatches.length === 0 ? (
        <div className="empty-state" style={{ textAlign: 'center', padding: '60px' }}>
          <Package size={48} opacity={0.3} style={{ margin: '0 auto 16px auto', color: 'var(--text-secondary)' }}/>
          <h3>No batches found.</h3>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {filteredBatches.map(batch => {
            const now = new Date();
            let statusBadge = "status-badge-small success";
            let statusText = "Fresh";
            if (batch.estimated_expiry_date) {
               const exp = new Date(batch.estimated_expiry_date);
               const diff = exp - now;
               if (diff < 0) { statusBadge = "status-badge-small danger"; statusText = "Expired"; }
               else if (diff < (3 * 24 * 60 * 60 * 1000)) { statusBadge = "status-badge-small warning"; statusText = "Near Expiry"; }
            }

            return (
              <div key={batch._id} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                      {batch.fruit_name} <span style={{fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 'normal'}}>({batch.category || 'Uncategorized'})</span>
                      {batch.is_active && <span className={statusBadge} style={{ fontSize: '0.7rem', padding: '2px 8px' }}>{statusText}</span>}
                      {batch.is_active && batch.quantity < 10 && <span className="status-badge-small danger" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>Low Stock</span>}
                    </h3>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', display: 'flex', gap: '16px', flexWrap: 'wrap', marginTop: '10px' }}>
                      <span><strong>ID:</strong> {batch.batch_id}</span>
                      <span><strong>Qty:</strong> {batch.quantity}</span>
                      <span><strong>Location:</strong> {batch.storage_location || 'Room Temp'}</span>
                      {batch.temperature !== undefined && batch.temperature !== null && <span><strong>Temp:</strong> {batch.temperature}°C</span>}
                      {batch.humidity !== undefined && batch.humidity !== null && <span><strong>Hum:</strong> {batch.humidity}%</span>}
                      <span><strong>Duration:</strong> {batch.storage_duration || '0 days'}</span>
                    </div>
                  </div>
                  {batch.is_active && (
                    <div style={{ display: 'flex', gap: '12px' }}>
                      {['Retail Manager', 'Warehouse Operator', 'Administrator', 'Admin', 'Retailer'].includes(userProfile?.role) && (
                        <button className="icon-btn" onClick={() => setEditingBatch(batch)} title="Edit Details"><Edit3 size={18}/></button>
                      )}
                      {['Retail Manager', 'Administrator', 'Admin', 'Retailer'].includes(userProfile?.role) && (
                        <button className="icon-btn danger" onClick={() => handleDelete(batch._id)} title="Delete"><Trash2 size={18}/></button>
                      )}
                    </div>
                  )}
                </div>

                {/* Shelf-Life & Compliance Panel */}
                {batch.is_active && (
                  <div style={{ padding: '16px', background: 'var(--bg-overlay)', borderRadius: '8px', borderLeft: `4px solid ${batch.storage_compliance === 'Compliant' ? 'var(--accent-primary)' : batch.storage_compliance === 'Warning' ? 'var(--warning)' : 'var(--danger)'}` }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                      
                      <div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Storage Compliance</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                          <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: batch.storage_compliance === 'Compliant' ? 'var(--accent-primary)' : batch.storage_compliance === 'Warning' ? 'var(--warning)' : 'var(--danger)' }}>
                            {batch.storage_compliance}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.85rem', marginTop: '8px' }}>
                          {batch.storage_optimization || 'Conditions are optimal.'}
                        </div>
                      </div>
                      
                      <div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Shelf-Life Prediction</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                          <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: batch.days_remaining !== null ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                            {batch.days_remaining !== null ? `${batch.days_remaining} Days Remaining` : 'Unknown'}
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                          <span style={{ fontSize: '0.75rem', padding: '2px 6px', background: 'var(--border-strong)', borderRadius: '4px' }}>Risk: {batch.risk_forecast || 'Unknown'}</span>
                          <span style={{ fontSize: '0.75rem', padding: '2px 6px', background: 'var(--border-strong)', borderRadius: '4px' }}>Trend: {batch.shelf_life_trend || 'Unknown'}</span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>AI Recommendations</span>
                        <div style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <div><strong style={{color: '#60a5fa'}}>Storage:</strong> {batch.storage_recommendation || 'N/A'}</div>
                          <div><strong style={{color: '#60a5fa'}}>Consumption:</strong> {batch.consumption_recommendation || 'N/A'}</div>
                          <div><strong style={{color: '#60a5fa'}}>Rotation:</strong> {batch.inventory_rotation_recommendation || 'N/A'}</div>
                          <div><strong style={{color: '#60a5fa'}}>Waste:</strong> {batch.waste_reduction_recommendation || 'N/A'}</div>
                          <div><strong style={{color: '#60a5fa'}}>Quality:</strong> {batch.quality_improvement_recommendation || 'N/A'}</div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Environmental History</span>
                        <div style={{ fontSize: '0.75rem', maxHeight: '60px', overflowY: 'auto' }}>
                          {batch.storage_history && batch.storage_history.length > 0 ? (
                            batch.storage_history.map((h, i) => (
                              <div key={i} style={{ padding: '2px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                                <span style={{ color: '#60a5fa' }}>{new Date(h.timestamp).toLocaleDateString()}</span> - {h.field} changed to {h.new} by {h.user}
                              </div>
                            ))
                          ) : (
                            <div style={{ color: '#555' }}>No history recorded.</div>
                          )}
                        </div>
                      </div>

                    </div>
                  </div>
                )}
              </div>
            );
          })}
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
             <button className="btn btn-secondary" disabled={skip === 0} onClick={() => setSkip(skip - limit)} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
               <ChevronLeft size={16} /> Previous
             </button>
             <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Page {Math.floor(skip/limit) + 1}</span>
             <button className="btn btn-secondary" disabled={batches.length < limit} onClick={() => setSkip(skip + limit)} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
               Next <ChevronRight size={16} />
             </button>
          </div>
        </div>
      )}

      <AnimatePresence>
        {showAddModal && <AddBatchModal onClose={() => setShowAddModal(false)} onSave={handleAddSave} isSubmitting={isSubmitting}/>}
        {editingBatch && <EditBatchModal batch={editingBatch} onClose={() => setEditingBatch(null)} onSave={handleEditSave} isSubmitting={isSubmitting}/>}
      </AnimatePresence>
    </div>
  );
};

export default Inventory;