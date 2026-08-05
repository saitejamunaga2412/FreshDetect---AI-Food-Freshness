import React, { useState, useEffect } from 'react';
import { Search, Info } from 'lucide-react';
import toast from 'react-hot-toast';

const API_URL = import.meta.env.VITE_API_URL;

const KnowledgeBase = () => {
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchFoods();
  }, []);

  const fetchFoods = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_URL}/api/knowledge-base/foods`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch knowledge base');
      const data = await res.json();
      setFoods(data);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredFoods = foods.filter(food => 
    food.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    food.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2>Food Knowledge Base</h2>
          <p>Reference guide for optimal storage conditions</p>
        </div>
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
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading knowledge base...</div>
      ) : filteredFoods.length === 0 ? (
        <div className="empty-state" style={{ textAlign: 'center', padding: '40px' }}>
          <Info size={48} color="var(--text-secondary)" style={{ margin: '0 auto 16px auto' }} />
          <h3>No items found</h3>
          <p style={{ color: 'var(--text-secondary)' }}>Try adjusting your search criteria</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
          {filteredFoods.map(food => (
            <div key={food._id || food.id} className="glass-card" style={{ padding: '20px' }}>
              <h3 style={{ margin: '0 0 4px 0', color: 'var(--accent-primary)' }}>{food.name}</h3>
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

              {food.spoilage_symptoms && food.spoilage_symptoms.length > 0 && (
                <div>
                  <p style={{ margin: '0 0 8px 0', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Spoilage Symptoms</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {food.spoilage_symptoms.map((sym, i) => (
                      <span key={i} style={{ background: 'rgba(239, 68, 68, 0.2)', color: 'var(--danger)', fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px' }}>
                        {sym}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default KnowledgeBase;
