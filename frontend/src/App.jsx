import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import KnowledgeBase from './pages/KnowledgeBase';
import Scanner from './pages/Scanner';
import Register from './pages/Register';
import Login from './pages/Login';
import Reports from './pages/Reports';
import Notifications from './pages/Notifications';
import Profile from './pages/Profile';
import About from './pages/About';
import Landing from './pages/Landing';
import ScanHistory from './pages/ScanHistory';
import Settings from './pages/Settings';

import AdminDashboard from './pages/AdminDashboard';
import AdminUsers from './pages/AdminUsers';
import AdminKnowledgeBase from './pages/AdminKnowledgeBase';

function App() {
  useEffect(() => {
    const saved = localStorage.getItem('freshdetect_settings');
    if (saved) {
      try {
        const prefs = JSON.parse(saved);
        if (prefs.theme === 'Dark') {
          document.documentElement.classList.add('dark-theme');
          document.documentElement.classList.remove('light-theme');
        } else if (prefs.theme === 'Light') {
          document.documentElement.classList.add('light-theme');
          document.documentElement.classList.remove('dark-theme');
        } else {
          document.documentElement.classList.remove('dark-theme', 'light-theme');
        }
      } catch (e) {}
    }
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    const wakeBackend = () => fetch(`${API_URL}/api/inventory`).catch(() => {});
    wakeBackend();
    const interval = setInterval(wakeBackend, 5 * 60 * 1000); // Every 5 minutes
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <Toaster position="top-right" toastOptions={{ style: { background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid #333' } }} />
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Authenticated Routes */}
          <Route element={<Layout />}>
            <Route element={<ProtectedRoute allowedRoles={['*']} />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/history" element={<ScanHistory />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/about" element={<About />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
            
            <Route element={<ProtectedRoute allowedRoles={['Retailer', 'Admin', 'Retail Manager', 'Warehouse Operator', 'Food Quality Inspector', 'Administrator']} />}>
              <Route path="/inventory" element={<Inventory />} />
              <Route path="/knowledge-base" element={<KnowledgeBase />} />
            </Route>
            
            <Route element={<ProtectedRoute allowedRoles={['Admin', 'Administrator']} />}>
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
              <Route path="/admin/users" element={<AdminUsers />} />
              <Route path="/admin/knowledge-base" element={<AdminKnowledgeBase />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;
