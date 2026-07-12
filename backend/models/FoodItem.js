const mongoose = require('mongoose');

const foodItemSchema = new mongoose.Schema({
  name: { type: String, required: true },
  category: { type: String, required: true },
  uploadDate: { type: Date, default: Date.now },
  expiryDate: { type: Date, required: true },
  freshnessScore: { type: Number, default: 100 }, // 0 to 100
  status: { type: String, enum: ['Fresh', 'Warning', 'Spoiled'], default: 'Fresh' },
  imageURL: { type: String },
  addedBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' }
}, { timestamps: true });

module.exports = mongoose.model('FoodItem', foodItemSchema);
