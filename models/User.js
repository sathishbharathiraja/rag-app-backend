const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  uid: { type: String, required: true, unique: true }, // Firebase UID
  email: { type: String, required: true, unique: true },
  displayName: { type: String, required: true },
  alias: { type: String }, // Custom nickname for chat
  avatarUrl: { type: String },
  lastSeen: { type: Date, default: Date.now },
  quietHours: { type: Boolean, default: false },
  muteAll: { type: Boolean, default: false },
});

module.exports = mongoose.model('User', userSchema);
