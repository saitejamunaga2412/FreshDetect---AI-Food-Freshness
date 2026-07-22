const express = require('express');
const router = express.Router();
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');

// Set up multer for handling memory storage (we'll forward it directly to Python)
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// AI Analysis Endpoint
router.post('/scan', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: 'No image uploaded' });
    }

    // Prepare form data to send to Python Microservice
    const formData = new FormData();
    formData.append('file', req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });

    // Call Python FastAPI service
    // Use Python service from environment variable or fallback to localhost
    const pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000';
    const pythonResponse = await axios.post(`${pythonApiUrl}/api/analyze`, formData, {
      headers: {
        ...formData.getHeaders(),
      }
    });

    const aiResult = pythonResponse.data.analysis;

    // Save to database if connected
    if (mongoose.connection.readyState === 1) {
        try {
            const newAnalysis = new Analysis({
                imagePath: req.file.path,
                result: aiResult,
                score: aiResult.score,
                status: aiResult.status,
                confidence: aiResult.confidence
            });
            await newAnalysis.save();
        } catch (dbErr) {
            console.warn("Could not save to DB:", dbErr);
        }
    } else {
        console.warn("Presentation Mode: Bypassing database save.");
    }

    res.json(aiResult);
  } catch (error) {
    console.error('Error during AI analysis:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    res.status(500).json({ message: 'Error connecting to AI analysis engine' });
  }
});

module.exports = router;
