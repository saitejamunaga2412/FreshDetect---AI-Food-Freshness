import React, { useState, useRef, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, PackageSearch, ScanLine, LogOut, FileBarChart, Bell, History, User, Info, Settings, Leaf } from 'lucide-react';
import './Layout.css';

const API_URL = import.meta.env.VITE_API_URL;

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  
  const [userProfile, setUserProfile] = useState({
    name: 'User',
    email: 'user@freshdetect.ai',
    avatarImage: null,
    avatar: 'U'
  });

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await fetch(`${API_URL}/api/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setUserProfile({
              name: data.name,
              email: data.email,
              avatarImage: data.avatarImage ? (data.avatarImage.startsWith('http') ? data.avatarImage : `${API_URL}${data.avatarImage}`) : null,
              avatar: data.name ? data.name.charAt(0).toUpperCase() : 'U',
              role: data.role
            });
          }
        } catch (err) {}
      }
    };
    fetchUser();
    
    window.addEventListener('profileUpdated', fetchUser);
    return () => window.removeEventListener('profileUpdated', fetchUser);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const pageTitles = {
    '/dashboard': 'Dashboard',
    '/scanner': 'Freshness Scanner',
    '/inventory': 'Inventory',
    '/history': 'Scan History',
    '/reports': 'Reports',
    '/notifications': 'Notifications',
    '/profile': 'Profile',
    '/about': 'About Project',
    '/settings': 'Settings'
  };

  const pageGreetings = {
    '/dashboard': "Today's Inventory Health",
    '/scanner': 'AI Freshness Analysis',
    '/inventory': 'Food Inventory Management',
    '/history': 'AI Prediction Logs',
    '/reports': 'Freshness Analytics',
    '/notifications': 'System Alerts',
    '/profile': 'User Profile',
    '/about': 'About FreshDetect',
    '/settings': 'Application Settings'
  };

  const currentTitle = pageTitles[location.pathname] || 'Dashboard';
  const currentGreeting = pageGreetings[location.pathname] || 'Monitor and manage your food freshness intelligently.';

  const MENU_CONFIG = [
    { title: 'Dashboard', icon: LayoutDashboard, route: '/dashboard', allowedRoles: ['*'] },
    { title: 'Admin Dashboard', icon: LayoutDashboard, route: '/admin/dashboard', allowedRoles: ['Admin', 'Administrator'] },
    { title: 'Users', icon: User, route: '/admin/users', allowedRoles: ['Admin', 'Administrator'] },
    { title: 'Knowledge Base', icon: Info, route: '/admin/knowledge-base', allowedRoles: ['Admin', 'Administrator'] },
    { title: 'Knowledge Base', icon: Info, route: '/knowledge-base', allowedRoles: ['Retailer', 'Retail Manager', 'Food Quality Inspector', 'Warehouse Operator'] },
    { title: 'Inventory', icon: PackageSearch, route: '/inventory', allowedRoles: ['Admin', 'Administrator', 'Retailer', 'Retail Manager', 'Warehouse Operator', 'Operator', 'Food Quality Inspector'] },
    { title: 'Freshness Scanner', icon: ScanLine, route: '/scanner', allowedRoles: ['*'] },
    { title: 'Scan History', icon: History, route: '/history', allowedRoles: ['*'] },
    { title: 'Reports', icon: FileBarChart, route: '/reports', allowedRoles: ['*'] },
    { title: 'Notifications', icon: Bell, route: '/notifications', allowedRoles: ['*'] },
    { title: 'Profile', icon: User, route: '/profile', allowedRoles: ['*'] },
    { title: 'Settings', icon: Settings, route: '/settings', allowedRoles: ['*'] },
    { title: 'About Project', icon: Info, route: '/about', allowedRoles: ['*'] }
  ];

  const hasAccess = (allowedRoles, userRole) => {
    if (!allowedRoles) return false;
    if (allowedRoles.includes('*')) return true;
    return allowedRoles.includes(userRole);
  };

  // ... (inside the component return, for the sidebar) ...
  // Wait, I am replacing lines 98 to 137. I need to include the <nav> rendering.

  return (
    <div className="app-layout">
      <aside className="sidebar glass-card" style={{ width: '300px' }}>
        <div className="logo-container" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
          <h2 style={{ fontSize: '1.75rem' }}><Leaf size={28} color="var(--accent-primary)" /> FreshDetect AI</h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.2 }}>Intelligent Food Freshness Monitoring Platform</span>
        </div>
        
        <nav className="nav-menu">
          {MENU_CONFIG.filter(item => hasAccess(item.allowedRoles, userProfile.role)).map((item, idx) => {
            const IconComponent = item.icon;
            return (
              <NavLink key={idx} to={item.route} className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
                <IconComponent size={20} /> {item.title}
              </NavLink>
            );
          })}
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
            <h1>{currentTitle}</h1>
            <p>{currentGreeting}</p>
          </div>
          <div className="profile-btn" ref={dropdownRef}>
            <div className="avatar" onClick={() => setDropdownOpen(!dropdownOpen)} style={{ overflow: 'hidden' }}>
              {userProfile.avatarImage ? (
                <img src={userProfile.avatarImage} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                userProfile.avatar
              )}
            </div>
            
            {dropdownOpen && (
              <div className="profile-dropdown">
                <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border-strong)', marginBottom: 4 }}>
                  <p style={{ fontWeight: 600, color: 'var(--text-primary)', margin: 0, fontSize: '0.9rem' }}>{userProfile.name}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0 }}>{userProfile.email}</p>
                </div>
                <button className="dropdown-item" onClick={() => { setDropdownOpen(false); navigate('/profile'); }}>
                  <User size={16} /> My Profile
                </button>
                <button className="dropdown-item" onClick={() => { setDropdownOpen(false); navigate('/settings'); }}>
                  <Settings size={16} /> Account Settings
                </button>
                <div className="dropdown-divider"></div>
                <button className="dropdown-item" style={{ color: 'var(--danger)' }} onClick={handleLogout}>
                  <LogOut size={16} /> Logout
                </button>
              </div>
            )}
          </div>
        </header>
        
        <div className="page-content animate-fade-in">
          <Outlet context={{ userProfile }} />
        </div>
      </main>
    </div>
  );
};

export default Layout;
