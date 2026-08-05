import React from 'react';
import { Target, Cpu, CheckCircle2, Layers, Zap, Camera, Activity, Database, Leaf, Info, PieChart, Heart, GitBranch, Terminal, Bell } from 'lucide-react';
import { motion } from 'framer-motion';
import './About.css';

export default function About() {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="about-wrapper animate-fade-in">
      <motion.div 
        className="about-layout"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {/* 1. Hero Section */}
        <motion.div className="about-hero" variants={itemVariants}>
          <Leaf size={48} className="text-emerald mb-4"/>
          <h1>FreshDetect AI</h1>
          <h2>AI-Powered Food Freshness Monitoring Platform</h2>
          <p>
            An intelligent computer vision ecosystem designed to reduce global food waste, optimize supply chains, 
            and guarantee quality through advanced YOLOv8 integration and predictive environmental ML.
          </p>
        </motion.div>

        {/* 2. Project Statistics */}
        <motion.div className="about-stats-grid" variants={itemVariants}>
          <div className="stat-card glass-card">
            <span className="stat-val text-emerald">10</span>
            <span className="stat-lbl">Total Modules</span>
          </div>
          <div className="stat-card glass-card">
            <span className="stat-val text-blue">MERN + Python</span>
            <span className="stat-lbl">Tech Stack</span>
          </div>
          <div className="stat-card glass-card">
            <span className="stat-val text-yellow">YOLOv8</span>
            <span className="stat-lbl">AI Vision Engine</span>
          </div>
          <div className="stat-card glass-card">
            <span className="stat-val text-grey">Phase 2</span>
            <span className="stat-lbl">Environmental ML Status</span>
          </div>
        </motion.div>

        {/* 3. Mission & Problem Statement */}
        <div className="about-columns">
          <motion.div className="glass-card flex-col gap-4 p-6" variants={itemVariants}>
            <div className="icon-badge bg-emerald"><Target size={24} color="var(--accent-primary)"/></div>
            <h3>Mission</h3>
            <p className="text-muted">
              To drastically reduce the billions of tons of food wasted annually. We aim to empower households, 
              grocers, and supply chains with accessible, real-time AI tools that eliminate manual visual inspection 
              errors and maximize shelf life efficiency.
            </p>
          </motion.div>

          <motion.div className="glass-card flex-col gap-4 p-6" variants={itemVariants}>
            <div className="icon-badge bg-yellow"><Info size={24} color="var(--warning)"/></div>
            <h3>Problem Statement & Solution</h3>
            <p className="text-muted">
              Visual inspection for spoilage is manual, error-prone, and painfully slow. FreshDetect solves this by 
              automating the classification and defect detection process. By combining YOLOv8 bounding boxes with 
              predictive models, we offer actionable storage recommendations instantly.
            </p>
          </motion.div>
        </div>

        {/* 4. System Architecture & AI Workflow */}
        <motion.div className="glass-card p-6" variants={itemVariants}>
          <h3 className="mb-4">System Architecture & Pipeline</h3>
          
          <div className="workflow-diagram">
            <div className="w-step">
              <div className="w-icon"><Camera size={24}/></div>
              <span>1. Image</span>
            </div>
            <span className="w-arrow">→</span>
            <div className="w-step">
              <div className="w-icon text-blue"><Cpu size={24}/></div>
              <span>2. YOLO Detection</span>
            </div>
            <span className="w-arrow">→</span>
            <div className="w-step">
              <div className="w-icon text-emerald"><Activity size={24}/></div>
              <span>3. Prediction</span>
            </div>
            <span className="w-arrow">→</span>
            <div className="w-step">
              <div className="w-icon text-yellow"><Database size={24}/></div>
              <span>4. Inventory</span>
            </div>
            <span className="w-arrow">→</span>
            <div className="w-step">
              <div className="w-icon text-blue"><PieChart size={24}/></div>
              <span>5. Reports</span>
            </div>
            <span className="w-arrow">→</span>
            <div className="w-step">
              <div className="w-icon text-red"><Bell size={24}/></div>
              <span>6. Notifications</span>
            </div>
            <span className="w-arrow">→</span>
            <div className="w-step">
              <div className="w-icon text-grey"><GitBranch size={24}/></div>
              <span>7. ML Pipeline</span>
            </div>
          </div>
          
          <div className="workflow-comparison" style={{marginTop: '32px', display: 'flex', gap: '24px'}}>
            <div className="glass-card" style={{flex: 1, padding: '16px', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)'}}>
              <h4 style={{color: '#3b82f6', marginBottom: '8px'}}>Current Pipeline</h4>
              <p className="text-muted text-sm">Image Upload → YOLOv8 Inference → Heuristic Freshness Scoring → Inventory Management</p>
            </div>
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              <span className="text-muted">→</span>
            </div>
            <div className="glass-card" style={{flex: 1, padding: '16px', background: 'rgba(245, 158, 11, 0.05)', border: '1px dashed rgba(245, 158, 11, 0.3)'}}>
              <h4 style={{color: 'var(--warning)', marginBottom: '8px'}}>Future Environmental ML Pipeline</h4>
              <p className="text-muted text-sm">YOLOv8 Identification + (Temp, Humidity, Storage, Packaging) → Scikit-Learn Predictive Expiry</p>
            </div>
          </div>
          
          <div className="workflow-explanation mt-6">
            <h4>How it works:</h4>
            <p className="text-muted text-sm mt-2">
              The user uploads a high-resolution image to the system. Our backend processes the payload using the 
              <strong> YOLOv8</strong> vision engine to draw bounding boxes and classify the produce. Surface defect analysis 
              determines an initial freshness score. The metadata is stored in <strong>MongoDB</strong>, populating the 
              Inventory, generating Executive Reports, and triggering prioritized Notifications. The final stage will 
              feed this data into a secondary <strong>Environmental ML model</strong>.
            </p>
          </div>
        </motion.div>

        {/* 5. Tech Stack & Key Features */}
        <div className="about-columns">
          <motion.div className="glass-card p-6 flex-col gap-4" variants={itemVariants}>
            <h3><Layers size={20} className="inline mr-2"/> Technology Stack</h3>
            <div className="tech-groups">
              <div className="tech-group">
                <h5>Frontend</h5>
                <p>React, Vite, CSS Modules</p>
              </div>
              <div className="tech-group">
                <h5>Backend</h5>
                <p>FastAPI, Python 3</p>
              </div>
              <div className="tech-group">
                <h5>Database</h5>
                <p>MongoDB (Motor Async)</p>
              </div>
              <div className="tech-group">
                <h5>Computer Vision</h5>
                <p>Ultralytics YOLOv8, OpenCV</p>
              </div>
              <div className="tech-group">
                <h5>Visualization</h5>
                <p>Recharts, Framer Motion</p>
              </div>
              <div className="tech-group pending-group">
                <h5>Future ML</h5>
                <p>Scikit-Learn (Environmental)</p>
              </div>
            </div>
          </motion.div>

          <motion.div className="flex-col gap-6" variants={itemVariants}>
            <div className="glass-card p-6">
              <h3 className="mb-4"><CheckCircle2 size={20} className="inline mr-2 text-emerald"/> Completed Modules</h3>
              <ul className="feature-list">
                <li><CheckCircle2 size={16} className="text-emerald"/> Landing Page & Auth Auth</li>
                <li><CheckCircle2 size={16} className="text-emerald"/> AI Dashboard</li>
                <li><CheckCircle2 size={16} className="text-emerald"/> YOLOv8 Vision Scanner</li>
                <li><CheckCircle2 size={16} className="text-emerald"/> Scan History Journal</li>
                <li><CheckCircle2 size={16} className="text-emerald"/> Intelligent Inventory</li>
                <li><CheckCircle2 size={16} className="text-emerald"/> Executive Reports</li>
                <li><CheckCircle2 size={16} className="text-emerald"/> Interactive Notifications</li>
                <li><CheckCircle2 size={16} className="text-emerald"/> AI Workspace Profile</li>
                <li><CheckCircle2 size={16} className="text-emerald"/> Control Center Settings</li>
              </ul>
            </div>
            
            <div className="glass-card p-6">
              <h3 className="mb-4"><Terminal size={20} className="inline mr-2 text-blue"/> Project Status</h3>
              <ul className="feature-list" style={{listStyle: 'none', padding: 0}}>
                <li style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)'}}>
                  <span style={{color: 'var(--text-secondary)'}}>Frontend ecosystem</span>
                  <span className="status-badge badge-green" style={{fontSize:'0.75rem'}}>Completed</span>
                </li>
                <li style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)'}}>
                  <span style={{color: 'var(--text-secondary)'}}>Backend APIs</span>
                  <span className="status-badge badge-green" style={{fontSize:'0.75rem'}}>Completed</span>
                </li>
                <li style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)'}}>
                  <span style={{color: 'var(--text-secondary)'}}>YOLOv8 Vision Model</span>
                  <span className="status-badge badge-green" style={{fontSize:'0.75rem'}}>Completed</span>
                </li>
                <li style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)'}}>
                  <span style={{color: 'var(--text-secondary)'}}>Environmental ML</span>
                  <span className="status-badge badge-yellow" style={{fontSize:'0.75rem'}}>Pending Next Phase</span>
                </li>
                <li style={{display: 'flex', justifyContent: 'space-between', padding: '8px 0'}}>
                  <span style={{color: 'var(--text-secondary)'}}>Cloud Deployment</span>
                  <span className="status-badge badge-grey" style={{fontSize:'0.75rem'}}>Future Phase</span>
                </li>
              </ul>
            </div>
          </motion.div>
        </div>

        {/* 6. Future Environmental ML Overview */}
        <motion.div className="glass-card p-6 bg-gradient-dark" variants={itemVariants}>
          <h3><Zap size={20} className="inline mr-2 text-yellow"/> The Future: Environmental ML Integration</h3>
          <p className="text-muted mt-2 mb-4">
            While YOLOv8 perfectly handles visual classification and defect detection, actual shelf life heavily depends on 
            surrounding conditions. Phase 2 of this project will integrate a secondary Machine Learning model trained to evaluate:
          </p>
          <div className="env-factors-grid">
            <div className="env-factor">
              <div className="e-dot bg-red"></div>
              <span>Ambient Temperature</span>
            </div>
            <div className="env-factor">
              <div className="e-dot bg-blue"></div>
              <span>Relative Humidity</span>
            </div>
            <div className="env-factor">
              <div className="e-dot bg-yellow"></div>
              <span>Storage Area (Crisper, Counter)</span>
            </div>
            <div className="env-factor">
              <div className="e-dot bg-emerald"></div>
              <span>Packaging Material</span>
            </div>
          </div>
          <p className="text-muted mt-4 text-sm border-t border-glass pt-4">
            By feeding these 4 metrics alongside the YOLO identification into our upcoming ML Model, FreshDetect will dynamically 
            predict exact <strong>Freshness Percentages</strong> and <strong>Shelf Life Expiry Dates</strong>, fully replacing 
            the current heuristic rules engine.
          </p>
        </motion.div>

        {/* 7. Credits */}
        <motion.div className="glass-card p-6 text-center credits-section" variants={itemVariants}>
          <Heart size={24} className="text-red mx-auto mb-2"/>
          <h3>Credits & Acknowledgements</h3>
          <p className="text-muted text-sm mt-2 max-w-lg mx-auto">
            FreshDetect AI was architected to push the boundaries of accessible computer vision in daily household management. 
            Thank you to the open-source communities behind React, FastAPI, MongoDB, and Ultralytics YOLO.
          </p>
        </motion.div>

      </motion.div>
    </div>
  );
}
