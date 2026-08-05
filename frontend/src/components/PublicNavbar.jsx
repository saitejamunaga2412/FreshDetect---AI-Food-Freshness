import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Leaf, Menu, X } from 'lucide-react';
import './PublicNavbar.css';

export default function PublicNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`public-navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="nav-container">
        <div className="nav-logo" onClick={() => navigate('/')}>
          <Leaf size={28} color="var(--accent-primary)" />
          <span>FreshDetect AI</span>
        </div>

        <div className="nav-links desktop-only">
          <a href="#how-it-works">How It Works</a>
          <a href="#features">Features</a>
          <a href="#architecture">Architecture</a>
        </div>

        <div className="nav-actions desktop-only">
          <NavLink to="/login" className="btn btn-secondary btn-sm">Login</NavLink>
          <NavLink to="/register" className="btn btn-primary btn-sm">Get Started</NavLink>
        </div>

        <button 
          className="mobile-menu-btn" 
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X size={24} color="#fafafa" aria-hidden="true" /> : <Menu size={24} color="#fafafa" aria-hidden="true" />}
        </button>
      </div>

      {mobileMenuOpen && (
        <div className="mobile-menu">
          <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)}>How It Works</a>
          <a href="#features" onClick={() => setMobileMenuOpen(false)}>Features</a>
          <a href="#architecture" onClick={() => setMobileMenuOpen(false)}>Architecture</a>
          <div className="mobile-actions">
            <NavLink to="/login" className="btn btn-secondary w-full" onClick={() => setMobileMenuOpen(false)}>Login</NavLink>
            <NavLink to="/register" className="btn btn-primary w-full" onClick={() => setMobileMenuOpen(false)}>Get Started</NavLink>
          </div>
        </div>
      )}
    </nav>
  );
}
