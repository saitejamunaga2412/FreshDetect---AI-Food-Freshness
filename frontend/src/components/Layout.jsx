import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, PackageSearch, ScanLine, LogOut } from 'lucide-react';
import './Layout.css';

const Layout = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Implement logout logic here
    navigate('/login');
  };

  return (
    <div className="app-layout">
      <aside className="sidebar glass-card">
        <div className="logo-container">
          <h2>FreshDetect</h2>
          <span className="badge badge-fresh">AI Powered</span>
        </div>
        
        <nav className="nav-menu">
          <NavLink to="/dashboard" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={20} /> Dashboard
          </NavLink>
          <NavLink to="/inventory" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <PackageSearch size={20} /> Inventory
          </NavLink>
          <NavLink to="/scanner" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
            <ScanLine size={20} /> Freshness Scanner
          </NavLink>
        </nav>
        
        <div className="sidebar-footer">
          <button className="btn btn-secondary w-full" onClick={handleLogout}>
            <LogOut size={18} /> Logout
          </button>
        </div>
      </aside>
      
      <main className="main-content">
        <header className="topbar">
          <div className="greeting">
            <h1>Welcome back, Admin</h1>
            <p>Here's what's happening with your inventory today.</p>
          </div>
          <div className="profile-btn">
            <div className="avatar">A</div>
          </div>
        </header>
        
        <div className="page-content animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
