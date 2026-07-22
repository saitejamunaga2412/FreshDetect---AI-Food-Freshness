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
          <div className="glass-card result-section animate-fade-in">
            <div className="result-header">
              <CheckCircle size={32} color="var(--success)" />
              <h2>Analysis Complete</h2>
            </div>
            
            <div className="result-details">
              <div className="result-stat">
                <span>Freshness Score</span>
                <strong style={{ color: result.score > 70 ? 'var(--success)' : 'var(--danger)' }}>
                  {result.score}%
                </strong>
              </div>
              <div className="result-stat">
                <span>Status</span>
                <span className={`badge badge-${result.status.toLowerCase()}`}>{result.status}</span>
              </div>
              <div className="result-stat">
                <span>AI Confidence</span>
                <strong>{result.confidence}%</strong>
              </div>
            </div>
            
            <button className="btn btn-primary w-full" style={{ marginTop: '24px' }}>Save to Inventory</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Scanner;
