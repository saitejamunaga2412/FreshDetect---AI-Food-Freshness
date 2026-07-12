import React, { useState } from 'react';
import { Plus, Search, Filter } from 'lucide-react';
import './Inventory.css';

const Inventory = () => {
  const [items] = useState([
    { id: 1, name: 'Fuji Apples', category: 'Fruit', status: 'Fresh', score: 95, expiry: '2026-07-20' },
    { id: 2, name: 'Roma Tomatoes', category: 'Vegetable', status: 'Warning', score: 45, expiry: '2026-07-13' },
    { id: 3, name: 'Baby Spinach', category: 'Vegetable', status: 'Spoiled', score: 10, expiry: '2026-07-10' },
    { id: 4, name: 'Avocados', category: 'Fruit', status: 'Fresh', score: 88, expiry: '2026-07-18' },
  ]);

  return (
    <div className="inventory-container">
      <div className="inventory-header">
        <div className="search-bar">
          <Search size={20} className="search-icon" />
          <input type="text" placeholder="Search inventory..." className="search-input" />
        </div>
        <div className="actions">
          <button className="btn btn-secondary"><Filter size={18} /> Filter</button>
          <button className="btn btn-primary"><Plus size={18} /> Add Item</button>
        </div>
      </div>

      <div className="glass-card table-container">
        <table className="inventory-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Freshness Score</th>
              <th>Status</th>
              <th>Expiry Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
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
                  <span className={`badge badge-${item.status.toLowerCase()}`}>{item.status}</span>
                </td>
                <td>{item.expiry}</td>
                <td>
                  <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Inventory;
