import React, { useEffect } from 'react';
import { motion, useAnimation } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Camera, Cpu, Activity, Database, Leaf, Shield, LineChart, Bell, Zap, Droplet } from 'lucide-react';
import PublicNavbar from '../components/PublicNavbar';
import './Landing.css';

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2
    }
  }
};

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="landing-page">
      <PublicNavbar />

      {/* Hero Section */}
      <section className="hero-section">
        <motion.div 
          className="hero-content"
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
        >
          <motion.div variants={fadeUp} className="badge-pill">
            <Zap size={14} color="var(--accent-primary)"/> Version 2.0 is now live
          </motion.div>
          <motion.h1 variants={fadeUp}>
            Intelligent Food Freshness <br/>
            <span className="text-gradient">Monitoring Platform</span>
          </motion.h1>
          <motion.p variants={fadeUp} className="hero-subtitle">
            Harness the power of YOLOv8 computer vision to eliminate food waste, predict shelf life, and optimize your inventory in real-time.
          </motion.p>
          <motion.div variants={fadeUp} className="hero-actions">
            <button className="btn btn-primary btn-lg" onClick={() => navigate('/register')}>Start Scanning Free</button>
            <button className="btn btn-secondary btn-lg" onClick={() => navigate('/dashboard')}>View Demo</button>
          </motion.div>
        </motion.div>
        
        <motion.div 
          className="hero-visual"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <div className="glass-card hero-dashboard-mockup">
            <div className="mockup-header">
              <div className="mockup-dots"><span></span><span></span><span></span></div>
              <div className="mockup-url">freshdetect.ai/dashboard</div>
            </div>
            <div className="mockup-body">
              <div className="mockup-sidebar"></div>
              <div className="mockup-content">
                <div className="mockup-cards">
                  <div className="m-card"></div>
                  <div className="m-card"></div>
                  <div className="m-card"></div>
                </div>
                <div className="mockup-chart"></div>
              </div>
            </div>
            
            {/* Floating Element */}
            <motion.div 
              className="floating-card"
              animate={{ y: [0, -10, 0] }}
              transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
            >
              <div className="f-header">
                <Leaf size={16} color="var(--accent-primary)"/>
                <span>Apple detected</span>
              </div>
              <div className="f-score">98% Fresh</div>
              <div className="f-sub">Est. Shelf Life: 7 days</div>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* Problem Statement */}
      <section className="problem-section" id="problem">
        <motion.div 
          className="section-header"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
        >
          <h2>Why Food Waste Matters</h2>
          <p>Over 1.3 billion tons of food is wasted globally every year due to improper storage and inability to detect early spoilage markers.</p>
        </motion.div>
        
        <motion.div 
          className="benefits-grid"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
        >
          <motion.div className="glass-card benefit-card" variants={fadeUp}>
            <div className="b-icon"><Droplet color="var(--danger)"/></div>
            <h3>Reduce Waste</h3>
            <p>Catch spoilage before it spreads and save thousands in lost inventory.</p>
          </motion.div>
          <motion.div className="glass-card benefit-card" variants={fadeUp}>
            <div className="b-icon"><Shield color="var(--accent-primary)"/></div>
            <h3>Improve Safety</h3>
            <p>Rely on objective AI analysis rather than error-prone manual visual inspections.</p>
          </motion.div>
          <motion.div className="glass-card benefit-card" variants={fadeUp}>
            <div className="b-icon"><LineChart color="#3b82f6"/></div>
            <h3>Save Money</h3>
            <p>Optimize shelf placement and storage conditions to maximize profitability.</p>
          </motion.div>
        </motion.div>
      </section>

      {/* How it Works / Architecture */}
      <section className="workflow-section" id="how-it-works">
        <motion.div 
          className="section-header"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
        >
          <h2>How FreshDetect Works</h2>
          <p>A seamless pipeline from camera lens to actionable dashboard insights.</p>
        </motion.div>

        <motion.div 
          className="workflow-container"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          variants={staggerContainer}
        >
          <div className="w-step">
            <motion.div className="w-icon-wrapper" variants={fadeUp}><Camera size={28} color="#fafafa"/></motion.div>
            <motion.h4 variants={fadeUp}>1. Image Upload</motion.h4>
            <motion.p variants={fadeUp}>Upload via web or capture directly using your mobile device.</motion.p>
          </div>
          <div className="w-connector"></div>
          <div className="w-step">
            <motion.div className="w-icon-wrapper" variants={fadeUp} style={{background: 'var(--accent-primary)'}}><Cpu size={28} color="var(--text-primary)"/></motion.div>
            <motion.h4 variants={fadeUp}>2. YOLO Detection</motion.h4>
            <motion.p variants={fadeUp}>AI isolates the produce and classifies the exact category instantly.</motion.p>
          </div>
          <div className="w-connector"></div>
          <div className="w-step">
            <motion.div className="w-icon-wrapper" variants={fadeUp}><Activity size={28} color="#fafafa"/></motion.div>
            <motion.h4 variants={fadeUp}>3. Freshness Scoring</motion.h4>
            <motion.p variants={fadeUp}>Deep learning assesses surface markers to predict remaining shelf life.</motion.p>
          </div>
          <div className="w-connector"></div>
          <div className="w-step">
            <motion.div className="w-icon-wrapper" variants={fadeUp}><Database size={28} color="#fafafa"/></motion.div>
            <motion.h4 variants={fadeUp}>4. Inventory Tracking</motion.h4>
            <motion.p variants={fadeUp}>Data is logged to MongoDB to generate weekly reports and alerts.</motion.p>
          </div>
        </motion.div>
      </section>

      {/* Tech Stack */}
      <section className="tech-section" id="architecture">
        <div className="glass-card tech-card">
          <div className="tech-content">
            <h2>Powered by Modern Tech</h2>
            <p>Built for scale, speed, and accuracy.</p>
            <div className="tech-tags">
              <span className="t-tag">React & Vite</span>
              <span className="t-tag">FastAPI</span>
              <span className="t-tag">MongoDB Async</span>
              <span className="t-tag">YOLOv8 Vision</span>
              <span className="t-tag">IoT Ready (Temp/Voc)</span>
            </div>
          </div>
          <div className="tech-graphic">
            {/* Abstract Graphic */}
            <div className="orbit-container">
              <div className="core">AI</div>
              <div className="orbit orbit-1"></div>
              <div className="orbit orbit-2"></div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <h2>Ready to eliminate food waste?</h2>
        <p>Join the next generation of smart kitchen and warehouse management.</p>
        <div className="cta-actions">
          <button className="btn btn-primary btn-lg" onClick={() => navigate('/register')}>Create Free Account</button>
        </div>
      </section>

      {/* Footer */}
      <footer className="public-footer">
        <div className="footer-content">
          <div className="f-logo">
            <Leaf size={24} color="var(--accent-primary)"/> FreshDetect AI
          </div>
          <div className="f-links">
            <span>© 2026 FreshDetect. All rights reserved.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
