import React, { useState, useEffect, useMemo, useRef } from 'react';
import { User, Mail, Shield, Activity, Camera, Edit2, History, MapPin, Phone } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import './Profile.css';

const API_URL = import.meta.env.VITE_API_URL;

export default function Profile() {
  const [loading, setLoading] = useState(true);
  const [inventoryData, setInventoryData] = useState([]);
  
  // Edit States
  const [isEditing, setIsEditing] = useState(false);
  const fileInputRef = useRef(null);
  const [isSaving, setIsSaving] = useState(false);

  const [profileData, setProfileData] = useState({
    name: "",
    email: "",
    phone: "",
    location: "",
    address: "",
    dob: "",
    gender: "",
    bio: "",
    role: "Staff",
    avatar: "U",
    avatarImage: null,
    memberSince: "2026"
  });

  const [editForm, setEditForm] = useState({...profileData});
  const [selectedAvatarFile, setSelectedAvatarFile] = useState(null);
  const [removeAvatarFlag, setRemoveAvatarFlag] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const fetchProfileData = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const authRes = await fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (authRes.ok) {
        const userData = await authRes.json();
        const pd = {
          name: userData.name || "",
          email: userData.email || "",
          phone: userData.phone || "",
          location: userData.location || "",
          address: userData.address || "",
          dob: userData.dob || "",
          gender: userData.gender || "",
          bio: userData.bio || "",
          role: userData.role || "Staff",
          avatar: userData.name ? userData.name.charAt(0).toUpperCase() : "U",
          avatarImage: userData.avatarImage ? (userData.avatarImage.startsWith('http') ? userData.avatarImage : `${API_URL}${userData.avatarImage}`) : null,
          memberSince: "2026"
        };
        setProfileData(pd);
        setEditForm(pd);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    const loadAllData = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      await fetchProfileData();

      try {
        const response = await fetch(`${API_URL}/api/inventory`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.ok) {
          const data = await response.json();
          setInventoryData(data);
        }
      } catch (err) {
        console.error("Failed to load inventory for profile:", err);
      } finally {
        setLoading(false);
      }
    };
    loadAllData();
  }, []);

  // Compute Metrics
  const metrics = useMemo(() => {
    const totalItems = inventoryData.length;
    let freshScoreTotal = 0;
    inventoryData.forEach(i => freshScoreTotal += (i.freshnessScore || 0));
    const avgFreshness = totalItems > 0 ? Math.round(freshScoreTotal / totalItems) : 0;
    
    let lastScanDate = "No scans yet";
    if (totalItems > 0) {
      const sorted = [...inventoryData].sort((a, b) => new Date(b.dateAdded || 0) - new Date(a.dateAdded || 0));
      if (sorted[0].dateAdded) {
        lastScanDate = new Date(sorted[0].dateAdded).toLocaleDateString();
      }
    }

    return { totalItems, avgFreshness, lastScanDate };
  }, [inventoryData]);

  const handleSaveProfile = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    setIsSaving(true);
    setUploadProgress(10);

    try {
      // 1. Upload or Remove Avatar
      if (removeAvatarFlag) {
        await fetch(`${API_URL}/api/auth/profile-picture`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
      } else if (selectedAvatarFile) {
        setUploadProgress(30);
        const formData = new FormData();
        formData.append('file', selectedAvatarFile);
        const uploadRes = await fetch(`${API_URL}/api/auth/profile-picture`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        });
        if (!uploadRes.ok) {
          throw new Error('Image upload failed');
        }
        setUploadProgress(70);
      }

      // 2. Update Profile Data
      const res = await fetch(`${API_URL}/api/auth/me`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          name: editForm.name,
          phone: editForm.phone,
          location: editForm.location,
          address: editForm.address,
          dob: editForm.dob,
          gender: editForm.gender,
          bio: editForm.bio
        })
      });

      setUploadProgress(100);

      if (res.ok) {
        await fetchProfileData(); // Refresh UI
        setIsEditing(false);
        setRemoveAvatarFlag(false);
        setSelectedAvatarFile(null);
        toast.success('Profile updated successfully!');
        window.dispatchEvent(new Event('profileUpdated')); // Sync top-right avatar
      } else {
        const data = await res.json();
        toast.error(data.detail || data.message || 'Failed to update profile');
      }
    } catch (e) {
      toast.error(e.message || 'Network error. Failed to save.');
    } finally {
      setIsSaving(false);
      setUploadProgress(0);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error("File size must be less than 5MB");
        return;
      }
      setSelectedAvatarFile(file);
      setRemoveAvatarFlag(false);
      const objectUrl = URL.createObjectURL(file);
      setEditForm(prev => ({ ...prev, avatarImage: objectUrl }));
      toast.success("Image selected. Click Save to upload!");
    }
  };

  const handleRemoveImage = () => {
    setSelectedAvatarFile(null);
    setRemoveAvatarFlag(true);
    setEditForm(prev => ({ ...prev, avatarImage: null }));
    toast.success("Image removed. Click Save to confirm.");
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  if (loading) {
    return (
      <div className="profile-wrapper">
        <div className="skeleton-box" style={{height: 200, borderRadius: 12}}></div>
        <div className="skeleton-box" style={{height: 400, borderRadius: 12, marginTop: 20}}></div>
      </div>
    );
  }

  return (
    <div className="profile-wrapper animate-fade-in">
      <motion.div 
        className="profile-layout"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {/* Left Column */}
        <div className="profile-sidebar">
          <motion.div className="glass-card user-card" variants={itemVariants}>
            <div className="avatar-wrapper">
              {(isEditing ? editForm.avatarImage : profileData.avatarImage) ? (
                <img 
                  src={isEditing ? editForm.avatarImage : profileData.avatarImage} 
                  alt="Profile" 
                  className="avatar-large" 
                  style={{objectFit: 'cover', borderRadius: '50%'}} 
                />
              ) : (
                <div className="avatar-large">{profileData.avatar}</div>
              )}
              {isEditing && (
                <>
                  <input 
                    type="file" 
                    accept="image/*" 
                    ref={fileInputRef} 
                    style={{display: 'none'}} 
                    onChange={handleImageUpload} 
                  />
                  <button className="edit-avatar-btn" aria-label="Edit Avatar" onClick={() => fileInputRef.current?.click()}>
                    <Camera size={16}/>
                  </button>
                  {editForm.avatarImage && (
                    <button className="edit-avatar-btn remove-btn" aria-label="Remove Avatar" onClick={handleRemoveImage} style={{ right: 'auto', left: 0, background: 'var(--danger)' }}>
                      &times;
                    </button>
                  )}
                </>
              )}
            </div>
            
            <h2>{profileData.name}</h2>
            <p className="user-role">{profileData.role}</p>
            
            <div className="user-details">
              <div className="detail-row">
                <Mail size={16} />
                <span>{profileData.email}</span>
              </div>
              <div className="detail-row">
                <Shield size={16} />
                <span className="text-emerald">Account Active</span>
              </div>
              <div className="detail-row">
                <History size={16} />
                <span>Member since {profileData.memberSince}</span>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="sidebar-quick-stats">
              <div className="qs-item">
                <span className="qs-lbl">Scans</span>
                <span className="qs-val">{metrics.totalItems}</span>
              </div>
              <div className="qs-item">
                <span className="qs-lbl">Freshness</span>
                <span className="qs-val">{metrics.avgFreshness}%</span>
              </div>
            </div>

            {!isEditing && (
              <button className="btn btn-secondary w-full mt-4" onClick={() => setIsEditing(true)}>
                <Edit2 size={16}/> Edit Profile
              </button>
            )}
          </motion.div>
        </div>

        {/* Right Column */}
        <div className="profile-main">
          {/* 1. Food Activity Summary KPIs */}
          <motion.div className="profile-section" variants={itemVariants}>
            <h3><Activity size={18}/> Food Activity Summary</h3>
            <div className="stats-grid-profile">
              <div className="stat-box glass-card border-green">
                <span className="stat-label">Total Scans</span>
                <span className="stat-value">{metrics.totalItems}</span>
              </div>
              <div className="stat-box glass-card border-blue">
                <span className="stat-label">Inventory Items</span>
                <span className="stat-value">{metrics.totalItems}</span>
              </div>
              <div className="stat-box glass-card border-yellow">
                <span className="stat-label">Avg Freshness</span>
                <span className="stat-value">{metrics.avgFreshness}%</span>
              </div>
              <div className="stat-box glass-card border-emerald">
                <span className="stat-label">Last Scan</span>
                <span className="stat-value" style={{fontSize: '1.2rem'}}>{metrics.lastScanDate}</span>
              </div>
            </div>
          </motion.div>

          {/* 2. User Information */}
          <motion.div className="profile-section" variants={itemVariants}>
            <div className="section-header">
              <h3><User size={18}/> User Information</h3>
              {isEditing && (
                <div style={{display:'flex', gap:'8px', alignItems:'center'}}>
                  <button className="btn btn-secondary btn-sm" onClick={() => {setIsEditing(false); setEditForm({...profileData});}}>Cancel</button>
                  <button className="btn btn-primary btn-sm" onClick={handleSaveProfile} disabled={isSaving}>
                    {isSaving ? "Saving..." : "Save Changes"}
                  </button>
                </div>
              )}
            </div>
            
            <div className="account-grid glass-card">
              <div className="info-group">
                <label><User size={14}/> Full Name</label>
                {isEditing ? (
                  <input type="text" className="edit-input" value={editForm.name} onChange={e => setEditForm({...editForm, name: e.target.value})} />
                ) : (
                  <p>{profileData.name || "Not Available"}</p>
                )}
              </div>
              <div className="info-group">
                <label><Mail size={14}/> Email</label>
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border-subtle)', minHeight: '44px'}}>
                  <span style={{fontSize: '1.05rem', color: 'var(--text-primary)'}}>{profileData.email}</span>
                  <span className="status-badge badge-green" style={{fontSize: '0.75rem', padding: '2px 8px'}}>Verified</span>
                </div>
                <small className="help-text">Email cannot be changed.</small>
              </div>
              <div className="info-group">
                <label><Phone size={14}/> Phone Number</label>
                {isEditing ? (
                  <input type="text" className="edit-input" placeholder="e.g. +1 234 567 8900" value={editForm.phone} onChange={e => setEditForm({...editForm, phone: e.target.value})} />
                ) : (
                  <p>{profileData.phone || "Not Available"}</p>
                )}
              </div>
              <div className="info-group">
                <label><MapPin size={14}/> Address / Location</label>
                {isEditing ? (
                  <input type="text" className="edit-input" placeholder="e.g. 123 Fresh Ave, NY" value={editForm.address || editForm.location} onChange={e => setEditForm({...editForm, address: e.target.value})} />
                ) : (
                  <p>{profileData.address || profileData.location || "Not Available"}</p>
                )}
              </div>
              <div className="info-group">
                <label>Date of Birth</label>
                {isEditing ? (
                  <input type="date" className="edit-input" value={editForm.dob} onChange={e => setEditForm({...editForm, dob: e.target.value})} />
                ) : (
                  <p>{profileData.dob || "Not Available"}</p>
                )}
              </div>
              <div className="info-group">
                <label>Gender</label>
                {isEditing ? (
                  <select className="edit-input" value={editForm.gender} onChange={e => setEditForm({...editForm, gender: e.target.value})}>
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                    <option value="Prefer not to say">Prefer not to say</option>
                  </select>
                ) : (
                  <p>{profileData.gender || "Not Available"}</p>
                )}
              </div>
              <div className="info-group" style={{gridColumn: '1 / -1'}}>
                <label>Bio / About Me</label>
                {isEditing ? (
                  <textarea className="edit-input" rows="3" placeholder="Tell us about yourself..." value={editForm.bio} onChange={e => setEditForm({...editForm, bio: e.target.value})} />
                ) : (
                  <p>{profileData.bio || "No bio provided yet."}</p>
                )}
              </div>
            </div>
            
            {uploadProgress > 0 && uploadProgress < 100 && (
              <div className="upload-progress-container" style={{marginTop: '15px'}}>
                <p style={{fontSize: '0.85rem', marginBottom: '5px', color: 'var(--text-secondary)'}}>Uploading... {uploadProgress}%</p>
                <div style={{height: '6px', width: '100%', background: 'var(--bg-card-hover)', borderRadius: '3px', overflow: 'hidden'}}>
                  <div style={{height: '100%', width: `${uploadProgress}%`, background: 'var(--primary)', transition: 'width 0.3s'}} />
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
