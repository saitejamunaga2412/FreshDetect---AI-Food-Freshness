const express = require('express');
const router = express.Router();
const FoodItem = require('../models/FoodItem');
const mongoose = require('mongoose');

// Enhanced Dummy data for presentation mode containing Phase 3 Recommendation logic
const DUMMY_INVENTORY = [
  { _id: '1', name: 'Apple', category: 'Fruits', status: 'Fresh', score: 95, batchId: 'B-001', location: 'A-1', 
    shelfLife: '30–45 Days', recommendation: 'Keep away from bananas and ethylene producers.' },
  { _id: '2', name: 'Banana', category: 'Fruits', status: 'Spoiled', score: 20, batchId: 'B-002', location: 'A-2',
    shelfLife: '0 Days', recommendation: 'Compost / Biogas processing.' },
  { _id: '3', name: 'Tomato', category: 'Vegetables', status: 'Near Expiry', score: 45, batchId: 'B-004', location: 'B-2',
    shelfLife: '2 Days', recommendation: 'Use immediately for soup or curry.' },
  { _id: '4', name: 'Carrot', category: 'Vegetables', status: 'Fresh', score: 90, batchId: 'B-003', location: 'B-1',
    shelfLife: '14-21 Days', recommendation: 'Store in refrigerator crisper drawer.' }
];

// Middleware to protect routes can be added here

// Get all inventory items
router.get('/', async (req, res) => {
  try {
    if (mongoose.connection.readyState !== 1) {
        return res.json(DUMMY_INVENTORY);
    }
    const items = await FoodItem.find().sort({ createdAt: -1 }).populate('addedBy', 'name');
    res.json(items);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Add new food item
router.post('/', async (req, res) => {
  try {
    const newItem = new FoodItem(req.body);
    await newItem.save();
    res.status(201).json(newItem);
  } catch (error) {
    res.status(400).json({ message: 'Error adding item', error: error.message });
  }
});

// Update food item
router.put('/:id', async (req, res) => {
  try {
    const updatedItem = await FoodItem.findByIdAndUpdate(req.params.id, req.body, { new: true });
    if (!updatedItem) return res.status(404).json({ message: 'Item not found' });
    res.json(updatedItem);
  } catch (error) {
    res.status(400).json({ message: 'Error updating item', error: error.message });
  }
});

// Delete food item
router.delete('/:id', async (req, res) => {
  try {
    const deletedItem = await FoodItem.findByIdAndDelete(req.params.id);
    if (!deletedItem) return res.status(404).json({ message: 'Item not found' });
    res.json({ message: 'Item deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

module.exports = router;
