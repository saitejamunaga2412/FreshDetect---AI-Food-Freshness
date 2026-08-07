import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  UploadCloud, Camera, CheckCircle2, X, Thermometer, Droplets, MapPin, Package, Clock, ShieldCheck, Activity, Brain, Image as ImageIcon, RotateCcw, AlertTriangle, FileWarning, Search, Bot, Lightbulb, Focus, Maximize
} from 'lucide-react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts';
import './Scanner.css';

const API_URL = import.meta.env.VITE_API_URL;

// Reusable Components
const PremiumErrorCard = ({ errorMsg, onClose }) => {
  let title = "Scanning Failed";
  let why = "An unexpected error occurred during processing.";
  let how = "Please try again later or check your network connection.";

  if (errorMsg.includes("No supported fruit")) {
    title = "Object Not Recognized";
    why = "Our AI model couldn't confidently identify a supported fruit or vegetable in this image.";
    how = "Ensure the item is well-lit, centered, and unobstructed before scanning again.";
  } else if (errorMsg.includes("Unsupported image format")) {
    title = "Invalid File Format";
    why = "The uploaded file is not a supported image type or the file headers are corrupted.";
    how = "Please upload a standard JPG, PNG, or WEBP image.";
  } else if (errorMsg.includes("too large")) {
    title = "File Too Large";
    why = "The uploaded image exceeds the 10MB processing limit.";
    how = "Compress the image or take a lower resolution photo and try again.";
  } else if (errorMsg.includes("Camera access")) {
    title = "Camera Access Denied";
    why = "Your browser blocked access to the camera, or no camera was found.";
    how = "Please allow camera permissions in your browser, or upload an image file instead.";
  } else {
    title = errorMsg;
  }

  return (
    <motion.div className="premium-error-card glass-card" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
      <button className="error-close" onClick={onClose} aria-label="Close Error"><X size={16} /></button>
      <div className="error-header">
        <div className="error-icon-wrapper"><AlertTriangle size={24} color="var(--danger)" /></div>
        <h3>{title}</h3>
      </div>
      <div className="error-body">
        <div className="error-row">
          <span className="error-label">What Happened:</span>
          <span className="error-text">Detection pipeline aborted.</span>
        </div>
        <div className="error-row">
          <span className="error-label">Why:</span>
          <span className="error-text">{why}</span>
        </div>
        <div className="error-row">
          <span className="error-label">Fix:</span>
          <span className="error-text">{how}</span>
        </div>
      </div>
    </motion.div>
  );
};

const RadialGauge = ({ value, label, color, subText, size = 160 }) => (
  <div className="gauge-wrapper" style={{ width: size, height: size }}>
    <ResponsiveContainer width="100%" height="100%">
      <RadialBarChart 
        cx="50%" cy="50%" 
        innerRadius="70%" outerRadius="100%" 
        barSize={12} data={[{ name: label, value: value, fill: color }]}
        startAngle={90} endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar background={{ fill: 'var(--border-subtle)' }} dataKey="value" cornerRadius={10} />
      </RadialBarChart>
    </ResponsiveContainer>
    <div className="gauge-center-text">
      <span className="g-value" style={{ color }}>{value}%</span>
      <span className="g-label">{label}</span>
      {subText && <span className="g-subtext">{subText}</span>}
    </div>
  </div>
);

const PipelineLoading = ({ currentStep }) => {
  const steps = [
    { id: 1, text: "Image Uploaded" },
    { id: 2, text: "Preparing Image" },
    { id: 3, text: "Running YOLO Detection" },
    { id: 4, text: "Predicting Freshness" },
    { id: 5, text: "FoodKeeper Lookup" },
    { id: 6, text: "Generating Recommendation" },
    { id: 7, text: "Completed" }
  ];

  return (
    <div className="pipeline-loader-wrapper">
      <div className="pipeline-loader" aria-live="polite">
        {steps.map((step) => {
          const isActive = currentStep === step.id;
          const isDone = currentStep > step.id;
          return (
            <div key={step.id} className={`pipeline-step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}>
              <div className="p-icon">
                {isDone ? <CheckCircle2 size={16}/> : isActive ? <div className="spinner"></div> : <div className="dot"></div>}
              </div>
              <span className="p-text">
                {step.text}{isActive ? '...' : ''}
                <span className="sr-only">{isActive ? 'in progress' : isDone ? 'completed' : 'pending'}</span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default function Scanner() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [result, setResult] = useState(null);
  const [scanId, setScanId] = useState(null);
  const [scanTime, setScanTime] = useState(0);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [errorDetail, setErrorDetail] = useState(null);
  
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveQuantity, setSaveQuantity] = useState(1);
  const [duplicateBatch, setDuplicateBatch] = useState(null);
  const [showSegmentation, setShowSegmentation] = useState(true);
  
  // Environmental Variables State
  const [envTemp, setEnvTemp] = useState(20.0);
  const [envHumid, setEnvHumid] = useState(50.0);
  const [savingInventory, setSavingInventory] = useState(false);
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    return () => stopCamera();
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleImageUpload = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file) => {
    setErrorMsg(null);
    setErrorDetail(null);
    if (!file.type.startsWith('image/')) {
      setErrorMsg("Unsupported file type.");
      setErrorDetail("Please upload JPG, PNG, or WEBP images under 5 MB.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg("File too large.");
      setErrorDetail("Maximum allowed size is 5MB. Please compress your image.");
      return;
    }
    setSelectedFile(file);
    setSelectedImage(URL.createObjectURL(file));
    setResult(null);
    setScanId(null);
  };

  const startCamera = async (e) => {
    e.stopPropagation();
    setErrorMsg(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      streamRef.current = stream;
      setIsCameraActive(true);
      setTimeout(() => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      }, 50);
    } catch (err) {
      console.error("Camera error:", err);
      setErrorMsg("Camera access denied.");
      setErrorDetail("Please ensure you have granted camera permissions in your browser settings.");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
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
      canvas.getContext("2d").drawImage(video, 0, 0);
      canvas.toBlob((blob) => {
        const file = new File([blob], "camera.jpg", { type: "image/jpeg" });
        processFile(file);
        stopCamera();
      }, "image/jpeg");
    }
  };

  const resetScanner = () => {
    setResult(null);
    setSelectedImage(null);
    setSelectedFile(null);
    setErrorMsg(null);
    setShowSegmentation(true);
  };

  const clearImage = (e) => {
    e.stopPropagation();
    setSelectedImage(null);
    setSelectedFile(null);
    setResult(null);
  };

  const runMockPipeline = () => {
    return new Promise(resolve => {
      let step = 1;
      const interval = setInterval(() => {
        step++;
        setLoadingStep(step);
        if (step >= 7) {
          clearInterval(interval);
          resolve();
        }
      }, 500);
    });
  };

  const handleScan = async () => {
    if (!selectedFile) return;
    setIsScanning(true);
    setLoadingStep(1);
    setErrorMsg(null);
    
    const startTime = performance.now();
    const pipelinePromise = runMockPipeline();
    
    try {
      const formData = new FormData();
      formData.append("image", selectedFile);
      formData.append("temp", envTemp);
      formData.append("humid", envHumid);
      
      const token = localStorage.getItem('token');
      
      const response = await axios.post(`${API_URL}/api/scanner/scan`, formData, {
        headers: { "Content-Type": "multipart/form-data", "Authorization": `Bearer ${token}` }
      });

      const apiResult = response.data.result;
      if (!apiResult || !apiResult.fruit) {
        throw new Error("No valid food detected in image.");
      }
      
      await pipelinePromise;
      
      const endTime = performance.now();
      setScanTime(((endTime - startTime) / 1000).toFixed(1));
      
      setResult(apiResult);
      if (response.data.scanId) setScanId(response.data.scanId);
    } catch (err) {
      console.error(err);
      
      const backendMessage = err.response?.data?.message || err.message;
      setErrorMsg(backendMessage);
      setResult(null);
    } finally {
      setIsScanning(false);
    }
  };



  // Helper mappings
  const getFreshnessColor = (category) => {
    switch (category) {
      case 'Fresh': return 'var(--accent-primary)';
      case 'Good': return 'var(--success)';
      case 'Acceptable': return '#fbbf24';
      case 'Near Spoilage': return 'var(--warning)';
      case 'Spoiled': return 'var(--danger)';
      default: return 'var(--text-secondary)';
    }
  };
  const getConfidenceText = (conf) => {
    return conf >= 0.9 ? 'Excellent Match' : conf >= 0.7 ? 'Good Match' : 'Uncertain';
  };



  const handleInitiateSave = async () => {
    if (!result) return;
    setSavingInventory(true);
    try {
      const token = localStorage.getItem('token');
      // Check duplicate using the GET endpoint with fruit_name
      const res = await axios.get(`${API_URL}/api/inventory/batches?status=active&fruit_name=${result.fruit}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.data && res.data.length > 0) {
        setDuplicateBatch(res.data[0]);
      } else {
        setDuplicateBatch(null);
      }
      setShowSaveModal(true);
    } catch (err) {
      console.error(err);
      alert("Failed to check inventory for duplicates.");
    } finally {
      setSavingInventory(false);
    }
  };

  const handleConfirmSave = async (isNewBatch) => {
    setSavingInventory(true);
    try {
      const token = localStorage.getItem('token');
      if (!isNewBatch && duplicateBatch) {
        // Increase quantity
        await axios.patch(`${API_URL}/api/inventory/batches/${duplicateBatch._id}`, {
          quantity: duplicateBatch.quantity + saveQuantity
        }, { headers: { "Authorization": `Bearer ${token}` } });
      } else {
        // Create new batch
        await axios.post(`${API_URL}/api/inventory/batches`, {
          batch_id: `BATCH-${Date.now()}`,
          fruit_name: result.fruit,
          category: 'Fruit',
          quantity: saveQuantity,
          storage_location: result.storage_area === 'Not Available' ? 'Room Temperature' : result.storage_area,
          temperature: result.recommended_temperature !== 'Not Available' ? parseFloat(result.recommended_temperature) : null,
          humidity: result.recommended_humidity !== 'Not Available' ? parseFloat(result.recommended_humidity) : null,
          visual_condition: result.weighted_scores?.visual_condition,
          environment_score: result.environment_score,
          overall_score: result.overall_score,
          final_status: result.freshness_category,
          confidence: result.confidence,
          yolo_class: result.yolo_class
        }, { headers: { "Authorization": `Bearer ${token}` } });
      }
      setShowSaveModal(false);
      alert("Successfully saved to inventory!");
    } catch (err) {
      console.error(err);
      alert("Failed to save to inventory.");
    } finally {
      setSavingInventory(false);
    }
  };

  return (
    <motion.div className="scanner-container" initial={{opacity:0}} animate={{opacity:1}}>
      <div className="scanner-header">
        <h2>AI Freshness Workstation</h2>
        <p>Identify food using computer vision and predict freshness using our environmental ML model.</p>
      </div>

      {errorMsg && (
        <div className="scanner-error-container">
          <PremiumErrorCard errorMsg={errorMsg} onClose={() => setErrorMsg(null)} />
        </div>
      )}

      <div className="scanner-layout">
        
        {/* LEFT COLUMN: THE LENS (Upload) */}
        <div className="scanner-panel lens-panel">
          <div className="panel-title">
            <Camera size={18}/> Image Input
          </div>

          <div 
            className={`lens-dropzone ${selectedImage || isCameraActive ? 'has-image' : ''} ${dragActive ? 'drag-active' : ''} ${isScanning ? 'scanning' : ''}`}
            onClick={() => !selectedImage && !isCameraActive && !isScanning && fileInputRef.current.click()}
            onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}
          >
            <input type="file" ref={fileInputRef} onChange={handleImageUpload} style={{ display: 'none' }} accept="image/*" aria-label="Upload food image"/>
            
            {isCameraActive ? (
              <div className="camera-view">
                <video ref={videoRef} autoPlay playsInline className="c-video"></video>
                <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
                <div className="camera-actions">
                  <button className="c-btn capture" onClick={captureImage}><Camera size={18}/> Capture</button>
                  <button className="c-btn close" onClick={(e) => { e.stopPropagation(); stopCamera(); }} aria-label="Close camera"><X size={18}/></button>
                </div>
              </div>
            ) : selectedImage ? (
              <div className="preview-view">
                <img 
                  src={result && result.segmented_image && showSegmentation ? `${API_URL}${result.segmented_image}` : selectedImage} 
                  alt="Uploaded food" 
                  className={`p-img ${isScanning ? 'img-scanning' : ''}`} 
                />
                
                {result && result.segmented_image && (
                  <div className="segmentation-toggle" style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 10 }}>
                    <button 
                      className={`glass-btn ${showSegmentation ? 'active-toggle' : ''}`} 
                      onClick={(e) => { e.stopPropagation(); setShowSegmentation(!showSegmentation); }}
                      style={{ background: showSegmentation ? 'var(--accent-primary)' : 'rgba(0,0,0,0.5)', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '20px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}
                    >
                      {showSegmentation ? 'Show Original' : 'Show Segmentation'}
                    </button>
                  </div>
                )}

                {!isScanning && (
                  <div className="preview-overlay">
                    <div className="overlay-actions">
                      <button className="glass-btn" onClick={(e) => { e.stopPropagation(); fileInputRef.current.click(); }}>
                        <RotateCcw size={16}/> Replace
                      </button>
                      <button className="glass-btn danger-glass" onClick={clearImage}>
                        <X size={16}/> Clear
                      </button>
                    </div>
                  </div>
                )}
                {isScanning && (
                  <div className="scan-beam-container" aria-hidden="true">
                    <div className="scan-beam"></div>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-upload">
                <div className="upload-circle"><ImageIcon size={32}/></div>
                <h3>Drag & Drop Image</h3>
                <p>or click to browse files</p>
                <span className="upload-hint">JPG, PNG, WEBP (Max 5MB)</span>
                <div className="camera-option">
                  <button className="glass-btn" onClick={startCamera}><Camera size={16}/> Use Camera</button>
                </div>
              </div>
            )}
          </div>

          {/* Environment Inputs */}
          <div className="env-inputs" style={{display: 'flex', gap: '1rem', marginTop: '1rem'}}>
            <div className="form-group" style={{flex: 1}}>
              <label>Current Temp (°C)</label>
              <input type="number" step="0.1" value={envTemp} onChange={(e) => setEnvTemp(e.target.value)} className="form-input" />
            </div>
            <div className="form-group" style={{flex: 1}}>
              <label>Current Humidity (%)</label>
              <input type="number" step="0.1" value={envHumid} onChange={(e) => setEnvHumid(e.target.value)} className="form-input" />
            </div>
          </div>

          <button 
            className="btn scan-btn"
            onClick={handleScan}
            disabled={!selectedImage || isScanning || isCameraActive}
            aria-busy={isScanning}
          >
            {isScanning ? 'AI Model Analyzing...' : 'Run Analysis'}
          </button>
        </div>

        {/* RIGHT COLUMN: WORKSTATION RESULTS */}
        <div className="scanner-panel result-panel">
          
          {!isScanning && !result ? (
            <div className="workstation-empty">
              <div className="empty-state-art">
                <Brain size={48} opacity={0.2}/>
              </div>
              <h3>Ready for Input</h3>
              <p>Upload a fruit or vegetable image to begin AI freshness analysis.</p>
              
              <div className="tips-box">
                <h4><Lightbulb size={14}/> Pro Tips</h4>
                <ul>
                  <li><Focus size={12}/> Keep the item centered</li>
                  <li><Lightbulb size={12}/> Use good lighting</li>
                  <li><Maximize size={12}/> Avoid blurry or far away images</li>
                </ul>
              </div>
            </div>
          ) : isScanning ? (
            <div className="workstation-loading">
              <Bot size={40} className="loading-bot"/>
              <h3>Analyzing Visual Data</h3>
              <PipelineLoading currentStep={loadingStep} />
            </div>
          ) : result ? (
            <motion.div className="workstation-results" initial={{opacity:0, y:20}} animate={{opacity:1, y:0}}>
              
              <div className="success-banner" aria-live="polite">
                <div className="sb-icon"><CheckCircle2 size={24} color="var(--accent-primary)"/></div>
                <div className="sb-text">
                  <strong>AI Analysis Complete</strong>
                  <span>Food Successfully Identified in {scanTime} seconds</span>
                </div>
              </div>

              {/* Gauges */}
              <div className="r-gauges">
                <div style={{position: 'relative'}} className="tooltip-parent">
                  <RadialGauge 
                    value={result.confidence ? parseFloat(result.confidence.replace('%', '')) : 0} 
                    label="Detection Confidence" 
                    color="#3b82f6" 
                    subText={getConfidenceText(result.confidence ? parseFloat(result.confidence.replace('%', '')) / 100 : 0)}
                  />
                  <span className="tooltip" style={{top: '10px', left: '10px', width: '180px', whiteSpace: 'normal', zIndex: 10}}>
                    Object Detection Confidence = How confident YOLO is about identifying the detected food.
                  </span>
                </div>
                <RadialGauge 
                  value={result.overall_score || 0} 
                  label="Predicted Freshness"
                  color={getFreshnessColor(result.freshness_category)} 
                  subText={result.freshness_category}
                />
              </div>

              {/* Assessment Breakdown Panel */}
              <div className="glass-card ai-explanation-card">
                <div className="card-top">
                  <span className="card-badge"><Brain size={14}/> Freshness Assessment Model</span>
                </div>
                <div className="ai-expl-grid">
                  <div className="expl-item">
                    <span className="expl-lbl">Detected Fruit</span>
                    <span className="expl-val">{result.fruit || "Unknown"}</span>
                  </div>
                  <div className="expl-item">
                    <span className="expl-lbl">Final Status</span>
                    <span className="expl-val" style={{color: getFreshnessColor(result.freshness_category)}}>
                      {result.freshness_category}
                    </span>
                  </div>
                  <div className="expl-item">
                    <span className="expl-lbl">Visual Condition</span>
                    <span className="expl-val" style={{ color: result.weighted_scores?.visual_condition?.toLowerCase() === 'rotten' ? 'var(--danger)' : 'var(--success)' }}>
                      {result.weighted_scores?.visual_condition || "Unknown"}
                    </span>
                  </div>
                  <div className="expl-item">
                    <span className="expl-lbl">Env. Freshness Score</span>
                    <span className="expl-val">{result.environment_score || 0}/100</span>
                  </div>
                  <div className="expl-item">
                    <span className="expl-lbl">Overall Freshness Score</span>
                    <span className="expl-val">{result.overall_score || 0}/100</span>
                  </div>
                </div>
              </div>

              {/* Storage Guidelines Panel */}
              <div className="glass-card ai-explanation-card" style={{ marginTop: '16px' }}>
                <div className="card-top">
                  <span className="card-badge"><Package size={14}/> USDA Storage Guidelines</span>
                </div>
                <div className="ai-expl-grid">
                  <div className="expl-item">
                    <span className="expl-lbl">Detected</span>
                    <span className="expl-val">{result.fruit || 'Unknown'}</span>
                  </div>
                  <div className="expl-item">
                    <span className="expl-lbl">Predicted Status</span>
                    <span className="expl-val" style={{color: getFreshnessColor(result.freshness_category)}}>
                      {result.freshness_category}
                    </span>
                  </div>
                </div>
                <div className="expl-reason">
                  <strong>Guideline:</strong>
                  <p>{result.storage_instructions}</p>
                </div>
                <div className="expl-footer">
                  <span className="expl-note">* Storage guidelines provided by the USDA FoodKeeper dataset.</span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="r-metrics-grid">
                <div className="m-card">
                  <span className="m-label">Recommended Storage Duration</span>
                  <div className="m-val" style={{fontSize: '0.9em', textAlign: 'left', marginTop: '4px'}}>
                    {result.shelf_life === "Not Available" || !result.shelf_life ? (
                      <span>Not Available</span>
                    ) : (
                      <ul style={{margin: 0, paddingLeft: '16px', listStyleType: 'disc'}}>
                        {Object.entries(result.shelf_life).map(([key, val]) => (
                          <li key={key}>
                            <span style={{textTransform: 'capitalize'}}>{key}</span>: {val}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
                <div className="m-card">
                  <span className="m-label">Recommended Conditions</span>
                  <div className="m-val" style={{fontSize: '0.9em', textAlign: 'left', marginTop: '4px'}}>
                    <Thermometer size={14} style={{display: 'inline', marginRight: '4px'}}/> Temp: {result.recommended_temperature}<br/>
                    <Droplets size={14} style={{display: 'inline', marginRight: '4px', marginTop: '4px'}}/> Humidity: {result.recommended_humidity}
                  </div>
                </div>
                <div className="m-card">
                  <span className="m-label">Overall Freshness Score</span>
                  <span className="m-val" style={{color: getFreshnessColor(result.freshness_category)}}>{result.overall_score}/100</span>
                </div>
              </div>



              {/* Actions */}
              <div className="r-actions">
                {user.role === 'Administrator' && (
                  <button className="btn scan-btn" onClick={handleInitiateSave} disabled={savingInventory} style={{ width: '100%', marginBottom: '12px' }}>
                    <Package size={18} style={{ marginRight: '8px' }}/> {savingInventory ? 'Processing...' : 'Save to Inventory'}
                  </button>
                )}
                <div className="secondary-actions" style={{ width: '100%', justifyContent: 'center' }}>
                  <button className="glass-btn-alt" onClick={resetScanner}>Scan Another</button>
                  <button className="glass-btn-alt" onClick={() => navigate('/history')}>View History</button>
                </div>
              </div>

            </motion.div>
          ) : null}
        </div>
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <div className="scanner-error-container" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setShowSaveModal(false)}>
          <div className="glass-card" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px', width: '90%', padding: '24px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px' }}>Save to Inventory</h3>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)', fontSize: '0.9em' }}>Quantity</label>
              <input 
                type="number" 
                min="1" 
                value={saveQuantity} 
                onChange={(e) => setSaveQuantity(parseInt(e.target.value) || 1)}
                style={{ width: '100%', padding: '10px', background: 'var(--bg-overlay)', border: '1px solid var(--border-strong)', color: 'var(--text-primary)', borderRadius: '6px' }}
              />
            </div>

            {duplicateBatch ? (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px', color: 'var(--danger)' }}>
                  <AlertTriangle size={18} style={{ marginRight: '8px' }}/>
                  <strong>Existing Batch Found</strong>
                </div>
                <p style={{ margin: 0, fontSize: '0.9em', color: 'var(--text-secondary)' }}>
                  An active batch of <strong>{duplicateBatch.fruit_name}</strong> already exists with {duplicateBatch.quantity} items.
                </p>
                <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                  <button onClick={() => handleConfirmSave(false)} className="btn scan-btn" style={{ flex: 1, padding: '8px', fontSize: '0.9em' }} disabled={savingInventory}>
                    Increase Quantity
                  </button>
                  <button onClick={() => handleConfirmSave(true)} className="glass-btn-alt" style={{ flex: 1, padding: '8px', fontSize: '0.9em' }} disabled={savingInventory}>
                    Create New
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={() => setShowSaveModal(false)} className="glass-btn-alt" style={{ flex: 1 }} disabled={savingInventory}>Cancel</button>
                <button onClick={() => handleConfirmSave(true)} className="btn scan-btn" style={{ flex: 1 }} disabled={savingInventory}>Save Item</button>
              </div>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}