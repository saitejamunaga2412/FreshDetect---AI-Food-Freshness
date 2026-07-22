import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Scanner from './pages/Scanner';
import Register from './pages/Register';
import Login from './pages/Login';

function App() {
  // Anti-sleep ping to keep Render backend awake
  useEffect(() => {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    const wakeBackend = () => fetch(`${API_URL}/api/inventory`).catch(() => {});
    wakeBackend();
    const interval = setInterval(wakeBackend, 5 * 60 * 1000); // Every 5 minutes
    return () => clearInterval(interval);
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="scanner" element={<Scanner />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
