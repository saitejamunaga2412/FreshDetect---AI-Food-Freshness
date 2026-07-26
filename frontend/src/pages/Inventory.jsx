import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter } from 'lucide-react';
import './Inventory.css';

const Inventory = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInventory = async () => {
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
        const response = await fetch(`${API_URL}/api/inventory`);
        if (response.ok) {
          const data = await response.json();
          setItems(data);
        }
      } catch (error) {
        console.error("Failed to fetch inventory:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchInventory();
  }, []);

  return (
    <div className="inventory-container">
      <div className="inventory-header">
        <div className="search-bar">
          <Search size={20} className="search-icon" />
          <input type="text" placeholder="Search inventory..." className="search-input" />
        </div>
        <div className="actions">
          <button className="btn btn-secondary"><Filter size={18} /> Filter</button>
          <button className="btn btn-primary" onClick={() => alert('Please use the Freshness Scanner page to automatically add items with AI analysis!')}>
            <Plus size={18} /> Add Item
          </button>
        </div>
      </div>

      <div className="glass-card table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading inventory...</div>
        ) : (
          <table className="inventory-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Freshness Score</th>
                <th>Status</th>
                <th>Shelf Life</th>
                <th>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item._id || Math.random()}>
                  <td><strong>{item.name}</strong></td>
                  <td>{item.category}</td>
                  <td>
                    <div className="score-bar-container">
                      <div className="score-bar" style={{ 
                        width: `${item.score}%`,
                        backgroundColor: item.score > 70 ? 'var(--success)' : item.score > 30 ? 'var(--warning)' : 'var(--danger)'
                      }}></div>
                    </div>
                    <span className="score-text">{item.score}%</span>
                  </td>
                  <td>
                    <span className={`badge badge-${item.status.toLowerCase().replace(' ', '-')}`}>{item.status}</span>
                  </td>
                  <td>{item.shelfLife || 'N/A'}</td>
                  <td style={{ maxWidth: '200px', fontSize: '0.85rem' }}>{item.recommendation || 'No recommendation'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Inventory;
