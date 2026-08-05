import React, { useEffect, useState } from 'react';
import { Navigate, Outlet, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const API_URL = import.meta.env.VITE_API_URL;

const ProtectedRoute = ({ allowedRoles }) => {
  const [authStatus, setAuthStatus] = useState('loading');
  const token = localStorage.getItem('token');
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      setAuthStatus('unauthenticated');
      return;
    }

    const checkRole = async () => {
      try {
        const res = await fetch(`${API_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          if (allowedRoles && (allowedRoles.includes('*') || allowedRoles.includes(data.role))) {
            setAuthStatus('authorized');
          } else {
            setAuthStatus('forbidden');
          }
        } else {
          setAuthStatus('unauthenticated');
          localStorage.removeItem('token'); // clear stale token
        }
      } catch (err) {
        setAuthStatus('unauthenticated');
      }
    };
    
    checkRole();
  }, [token, allowedRoles]);

  if (authStatus === 'loading') {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: 'var(--bg-primary)', color: 'var(--accent-primary)' }}>
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h3>Authenticating...</h3>
        </div>
      </div>
    );
  }

  if (authStatus === 'unauthenticated') {
    return <Navigate to="/login" replace />;
  }

  if (authStatus === 'forbidden') {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: 'var(--bg-primary)', color: 'var(--danger)' }}>
        <div style={{ padding: '40px', textAlign: 'center', backgroundColor: 'var(--bg-secondary)', borderRadius: '12px', border: '1px solid #334155' }}>
          <h1 style={{ fontSize: '3rem', marginBottom: '10px' }}>403</h1>
          <h3 style={{ fontSize: '1.5rem', marginBottom: '20px' }}>Forbidden</h3>
          <p style={{ color: '#94a3b8', marginBottom: '20px' }}>You do not have permission to access this page.</p>
          <button 
            onClick={() => navigate(-1)} 
            style={{ display: 'inline-block', padding: '10px 20px', backgroundColor: '#3b82f6', color: 'var(--text-primary)', border: 'none', cursor: 'pointer', borderRadius: '6px', fontWeight: 'bold' }}>
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return <Outlet />;
};

export default ProtectedRoute;
