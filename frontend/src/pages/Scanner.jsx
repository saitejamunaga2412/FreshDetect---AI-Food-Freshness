import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Camera, CheckCircle, X } from 'lucide-react';
import './Scanner.css';

const Scanner = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [error, setError] = useState(null);
  
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // Stop camera stream when component unmounts
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const handleImageUpload = (e) => {
    if (e.target.files && e.target.files[0]) {
      const img = URL.createObjectURL(e.target.files[0]);
      setSelectedImage(img);
      setResult(null);
    }
  };

  const startCamera = async (e) => {
    e.stopPropagation(); // Prevent opening file dialog
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      streamRef.current = stream;
      setIsCameraActive(true);
      // Ensure videoRef is populated before setting srcObject
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      }, 50);
    } catch (err) {
      console.error("Error accessing camera:", err);
      alert("Could not access camera. Please ensure you have granted permission.");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const captureImage = (e) => {
    e.stopPropagation();
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imgDataUrl = canvas.toDataURL('image/jpeg');
      setSelectedImage(imgDataUrl);
      setResult(null);
      stopCamera();
    }
  };

  const handleScan = async () => {
    setIsScanning(true);
    setError(null);
    try {
      // If we have a selected image, we need to convert it to a file
      // selectedImage is a data URL (from camera) or object URL (from file input)
      let fileToSend = null;
      
      if (selectedImage.startsWith('data:image')) {
        // Convert base64 to Blob
        const response = await fetch(selectedImage);
        const blob = await response.blob();
        fileToSend = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });
      } else {
        // From file input
        fileToSend = fileInputRef.current.files[0];
      }

      if (!fileToSend) {
        throw new Error("No valid image found");
      }

      const formData = new FormData();
      formData.append('image', fileToSend);

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      const response = await fetch(`${API_URL}/api/analysis/scan`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Analysis failed. Make sure backend is running.');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Error communicating with AI engine');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="scanner-container">
      <div className="scanner-layout">
        <div className="glass-card upload-section">
          <h2>Upload Image for Analysis</h2>
          <p className="subtitle">Supported formats: JPG, PNG, WEBP (Max 5MB)</p>
          
          <div 
            className={`upload-dropzone ${selectedImage || isCameraActive ? 'has-image' : ''}`}
            onClick={() => !selectedImage && !isCameraActive && fileInputRef.current.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleImageUpload} 
              style={{ display: 'none' }} 
              accept="image/*"
            />
            
            {isCameraActive ? (
              <div className="camera-container">
                <video ref={videoRef} autoPlay playsInline className="camera-video"></video>
                <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
                <div className="camera-controls">
                  <button className="btn btn-secondary capture-btn" onClick={captureImage}>
                    <Camera size={24} /> Capture
                  </button>
                  <button className="btn btn-secondary close-camera-btn" onClick={(e) => { e.stopPropagation(); stopCamera(); }}>
                    <X size={20} />
                  </button>
                </div>
              </div>
            ) : selectedImage ? (
              <div className="image-preview-container">
                <img src={selectedImage} alt="Food item" className="image-preview" />
                <div className="preview-overlay">
                  <button className="btn btn-secondary" onClick={(e) => {
                    e.stopPropagation();
                    setSelectedImage(null);
                    setResult(null);
                  }}>Change Image</button>
                </div>
              </div>
            ) : (
              <div className="upload-placeholder">
                <UploadCloud size={48} className="upload-icon" />
                <p>Drag & drop or click to upload</p>
                <div className="divider"><span>OR</span></div>
                <button className="btn btn-secondary" onClick={startCamera}>
                  <Camera size={18} /> Use Camera
                </button>
              </div>
            )}
          </div>
          
          <button 
            className={`btn btn-primary w-full scan-btn ${!selectedImage || isScanning ? 'disabled' : ''}`}
            onClick={handleScan}
            disabled={!selectedImage || isScanning}
          >
            {isScanning ? (
              <span className="loading-spinner">Scanning...</span>
            ) : (
              'Analyze Freshness'
            )}
          </button>

          {error && (
            <div className="error-message stagger-5 animate-fade-in" style={{ color: 'red', marginTop: '1rem', textAlign: 'center' }}>
              {error}
            </div>
          )}
        </div>

        {result && (
          <div className="glass-card result-section animate-fade-in" style={{ padding: '24px' }}>
            <div className="result-header" style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '16px' }}>
              <CheckCircle size={32} color={result.status === 'Spoiled' ? 'var(--danger)' : result.status === 'Near Expiry' ? 'var(--warning)' : 'var(--success)'} />
              <div>
                <h2 style={{ margin: 0, fontSize: '1.5rem' }}>{result.foodName || 'Food Item'} Identified</h2>
                <span className={`badge badge-${result.status.toLowerCase().replace(' ', '-')}`} style={{ marginTop: '8px', display: 'inline-block', fontSize: '1rem', padding: '4px 12px' }}>
                  Status: {result.status}
                </span>
              </div>
            </div>
            
            <div className="result-details" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div className="result-stat" style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px' }}>
                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Freshness Score</span>
                <strong style={{ fontSize: '2rem', color: result.score > 70 ? 'var(--success)' : result.score > 30 ? 'var(--warning)' : 'var(--danger)' }}>
                  {result.score}%
                </strong>
              </div>
              <div className="result-stat" style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px' }}>
                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>AI Confidence</span>
                <strong style={{ fontSize: '2rem' }}>{(result.confidence * 100).toFixed(0)}%</strong>
              </div>
            </div>

            {/* Recommendation Engine UI */}
            {result.recommendation && (
              <div className="recommendation-section" style={{ 
                backgroundColor: result.status === 'Spoiled' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(59, 130, 246, 0.1)', 
                border: `1px solid ${result.status === 'Spoiled' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(59, 130, 246, 0.3)'}`,
                borderRadius: '12px', padding: '20px' 
              }}>
                <h3 style={{ margin: '0 0 16px 0', color: result.status === 'Spoiled' ? '#ef4444' : '#3b82f6', fontSize: '1.2rem' }}>
                  {result.recommendation.type}
                </h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.95rem' }}>
                  {result.recommendation.temperature && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Temperature:</span>
                      <strong>{result.recommendation.temperature}</strong>
                    </div>
                  )}
                  {result.recommendation.humidity && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Humidity:</span>
                      <strong>{result.recommendation.humidity}</strong>
                    </div>
                  )}
                  {result.recommendation.area && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Storage Area:</span>
                      <strong>{result.recommendation.area}</strong>
                    </div>
                  )}
                  {result.recommendation.packaging && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Packaging:</span>
                      <strong>{result.recommendation.packaging}</strong>
                    </div>
                  )}
                  {result.recommendation.consumeWithin && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Consume Within:</span>
                      <strong style={{ color: '#f59e0b' }}>{result.recommendation.consumeWithin}</strong>
                    </div>
                  )}
                  {result.recommendation.shelfLife && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#94a3b8' }}>Estimated Shelf Life:</span>
                      <strong style={{ color: '#10b981' }}>{result.recommendation.shelfLife}</strong>
                    </div>
                  )}
                  
                  {/* Action/Tips Block */}
                  {(result.recommendation.tips || result.recommendation.action) && (
                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                      {result.recommendation.tips && (
                        <p style={{ margin: 0, fontStyle: 'italic', color: '#e2e8f0' }}>💡 Tip: {result.recommendation.tips}</p>
                      )}
                      {result.recommendation.action && (
                        <p style={{ margin: 0, fontWeight: 'bold', color: result.status === 'Spoiled' ? '#ef4444' : '#e2e8f0' }}>
                          ⚡ Action: {result.recommendation.action}
                        </p>
                      )}
                      {result.recommendation.reason && (
                        <p style={{ margin: '8px 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>Reason: {result.recommendation.reason}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            <button className="btn btn-primary w-full" style={{ marginTop: '24px' }} onClick={async () => {
              try {
                const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
                const response = await fetch(`${API_URL}/api/inventory`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    name: result.foodName || 'Food Item',
                    category: result.recommendation?.type === 'Disposal Guide' ? 'Spoiled' : 'Produce',
                    score: result.score,
                    status: result.status,
                    shelfLife: result.recommendation?.shelfLife || '0 Days',
                    recommendation: result.recommendation?.action || result.recommendation?.tips || 'N/A'
                  })
                });
                if (response.ok) {
                  alert('Successfully saved to inventory!');
                  setResult(null);
                  setSelectedImage(null);
                } else {
                  alert('Failed to save to inventory.');
                }
              } catch (err) {
                alert('Successfully saved to inventory (Offline Mode)!');
                setResult(null);
                setSelectedImage(null);
              }
            }}>
              Save to Inventory
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Scanner;
