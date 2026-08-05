import React, { useState, useEffect } from 'react';
import { Search, Info, Plus, Edit2, Trash2, X } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = import.meta.env.VITE_API_URL;

const AdminKnowledgeBase = () => {
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [currentFood, setCurrentFood] = useState({
    name: '', category: '', ideal_temperature: '', ideal_humidity: '',
    shelf_life_days: '', spoilage_symptoms: ''
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchFoods();
  }, []);

  const fetchFoods = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/api/knowledge-base`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFoods(res.data);
    } catch (err) {
      toast.error("Failed to load knowledge base");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this produce?")) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/knowledge-base/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Deleted successfully");
      fetchFoods();
    } catch (err) {
      toast.error("Failed to delete item");
    }
  };

  const openModal = (mode, food = null) => {
    setModalMode(mode);
    if (mode === 'edit' && food) {
      setCurrentFood({
        ...food,
        spoilage_symptoms: food.spoilage_symptoms ? food.spoilage_symptoms.join(', ') : ''
      });
    } else {
      setCurrentFood({
        name: '', category: '', ideal_temperature: '', ideal_humidity: '',
        shelf_life_days: '', spoilage_symptoms: ''
      });
    }
    setIsModalOpen(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const token = localStorage.getItem('token');
      const payload = {
        name: currentFood.name,
        category: currentFood.category,
        ideal_temperature: Number(currentFood.ideal_temperature),
        ideal_humidity: Number(currentFood.ideal_humidity),
        shelf_life_days: Number(currentFood.shelf_life_days),
        spoilage_symptoms: currentFood.spoilage_symptoms ? currentFood.spoilage_symptoms.split(',').map(s => s.trim()).filter(s => s) : []
      };

      if (modalMode === 'add') {
        await axios.post(`${API_URL}/api/knowledge-base`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Added successfully");
      } else {
        const id = currentFood._id || currentFood.id;
        await axios.put(`${API_URL}/api/knowledge-base/${id}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success("Updated successfully");
      }
      
      setIsModalOpen(false);
      fetchFoods();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to save item");
    } finally {
      setIsSaving(false);
    }
  };

  const filteredFoods = foods.filter(food => 
    food.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    food.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header" style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: '0 0 8px 0' }}>Knowledge Base Management</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Administer food storage guidelines.</p>
        </div>
        <button className="btn btn-primary" onClick={() => openModal('add')}>
          <Plus size={18} /> Add Produce
        </button>
      </div>

      <div className="glass-card" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--text-secondary)' }} />
            <input 
              type="text" 
              className="form-input" 
              placeholder="Search produce..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '38px', width: '100%' }}
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading...</div>
      ) : filteredFoods.length === 0 ? (
        <div className="empty-state" style={{ textAlign: 'center', padding: '60px', background: 'var(--bg-overlay)', borderRadius: '12px', border: '1px dashed var(--border-strong)' }}>
          <Info size={48} color="var(--text-secondary)" style={{ margin: '0 auto 16px auto', opacity: 0.5 }} />
          <h3 style={{ marginBottom: '8px' }}>Knowledge Base is Empty</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto 24px auto' }}>
            The AI relies on the Knowledge Base to provide accurate storage guidelines and shelf-life predictions. 
            {searchTerm ? " No items match your search criteria." : " Add your first produce item to start building the database."}
          </p>
          {!searchTerm && (
            <button className="btn btn-primary" onClick={() => openModal('add')}>
              <Plus size={18} /> Add Your First Item
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
          {filteredFoods.map(food => (
            <div key={food._id || food.id} className="glass-card" style={{ padding: '20px', position: 'relative' }}>
              <div style={{ position: 'absolute', top: '20px', right: '20px', display: 'flex', gap: '8px' }}>
                <button onClick={() => openModal('edit', food)} style={{ background: 'transparent', border: 'none', color: '#3b82f6', cursor: 'pointer' }}>
                  <Edit2 size={16} />
                </button>
                <button onClick={() => handleDelete(food._id || food.id)} style={{ background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>
                  <Trash2 size={16} />
                </button>
              </div>
              <h3 style={{ margin: '0 0 4px 0', color: 'var(--accent-primary)', paddingRight: '50px' }}>{food.name}</h3>
              <p style={{ margin: '0 0 16px 0', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{food.category}</p>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div style={{ background: 'var(--border-subtle)', padding: '10px', borderRadius: '8px' }}>
                  <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Temp</p>
                  <p style={{ margin: 0, fontWeight: 'bold' }}>{food.ideal_temperature}°C</p>
                </div>
                <div style={{ background: 'var(--border-subtle)', padding: '10px', borderRadius: '8px' }}>
                  <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Humidity</p>
                  <p style={{ margin: 0, fontWeight: 'bold' }}>{food.ideal_humidity}%</p>
                </div>
              </div>
              
              <div style={{ background: 'var(--border-subtle)', padding: '10px', borderRadius: '8px', marginBottom: '16px' }}>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Shelf Life</p>
                <p style={{ margin: 0, fontWeight: 'bold' }}>{food.shelf_life_days} Days</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {isModalOpen && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="glass-card" style={{ width: '100%', maxWidth: '500px', padding: '24px', position: 'relative' }}>
            <button onClick={() => setIsModalOpen(false)} style={{ position: 'absolute', top: '24px', right: '24px', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
              <X size={24} />
            </button>
            <h3 style={{ margin: '0 0 20px 0' }}>{modalMode === 'add' ? 'Add Produce' : 'Edit Produce'}</h3>
            
            <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label className="form-label">Produce Name</label>
                <input required type="text" className="form-input" value={currentFood.name} onChange={(e) => setCurrentFood({...currentFood, name: e.target.value})} />
              </div>
              <div>
                <label className="form-label">Category</label>
                <input required type="text" className="form-input" value={currentFood.category} onChange={(e) => setCurrentFood({...currentFood, category: e.target.value})} />
              </div>
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label">Ideal Temp (°C)</label>
                  <input required type="number" step="0.1" className="form-input" value={currentFood.ideal_temperature} onChange={(e) => setCurrentFood({...currentFood, ideal_temperature: e.target.value})} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label">Ideal Humidity (%)</label>
                  <input required type="number" className="form-input" value={currentFood.ideal_humidity} onChange={(e) => setCurrentFood({...currentFood, ideal_humidity: e.target.value})} />
                </div>
              </div>
              <div>
                <label className="form-label">Shelf Life (Days)</label>
                <input required type="number" className="form-input" value={currentFood.shelf_life_days} onChange={(e) => setCurrentFood({...currentFood, shelf_life_days: e.target.value})} />
              </div>
              <div>
                <label className="form-label">Spoilage Symptoms (comma separated)</label>
                <input type="text" className="form-input" value={currentFood.spoilage_symptoms} onChange={(e) => setCurrentFood({...currentFood, spoilage_symptoms: e.target.value})} placeholder="e.g. Soft spots, Mold, Bad odor" />
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminKnowledgeBase;
