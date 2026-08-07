import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Lock, Mail, Shield } from 'lucide-react';
import './Register.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Consumer');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password, role }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Registration successful
        navigate('/login');
      } else {
        // Registration failed
        setError(data.message || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-background"></div>
      
      <div className="glass-card register-card animate-fade-in">
        <div className="register-header stagger-1 animate-fade-in">
          <h2>Create Account</h2>
          <p>Join the FreshDetect platform</p>
        </div>
        
        {error && (
          <div className="stagger-1 animate-fade-in" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: 'var(--danger)', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.9rem', border: '1px solid rgba(239, 68, 68, 0.5)' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleRegister} className="register-form">
          <div className="input-group stagger-2 animate-fade-in">
            <label className="input-label">Full Name</label>
            <div className="input-with-icon">
              <User size={18} className="input-icon" />
              <input 
                type="text" 
                className="input-field" 
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required 
              />
            </div>
          </div>

          <div className="input-group stagger-3 animate-fade-in">
            <label className="input-label">Email Address</label>
            <div className="input-with-icon">
              <Mail size={18} className="input-icon" />
              <input 
                type="email" 
                className="input-field" 
                placeholder="admin@freshdetect.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required 
              />
            </div>
          </div>
          
          <div className="input-group stagger-4 animate-fade-in">
            <label className="input-label">Password</label>
            <div className="input-with-icon">
              <Lock size={18} className="input-icon" />
              <input 
                type="password" 
                className="input-field" 
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
              />
            </div>
          </div>

          <div className="input-group stagger-5 animate-fade-in">
            <label className="input-label">Role</label>
            <div className="input-with-icon">
              <Shield size={18} className="input-icon" />
              <select 
                className="input-field custom-select"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="Consumer">Consumer</option>
                <option value="Retail Manager">Retail Manager</option>
                <option value="Warehouse Operator">Warehouse Operator</option>
                <option value="Food Quality Inspector">Food Quality Inspector</option>
                <option value="Administrator">Administrator</option>
              </select>
            </div>
          </div>
          
          <button type="submit" className="btn btn-primary register-btn stagger-5 animate-fade-in w-full" disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <div className="register-footer stagger-5 animate-fade-in">
          <p>Already have an account? <Link to="/login">Sign in here</Link></p>
        </div>
      </div>
    </div>
  );
};

export default Register;
