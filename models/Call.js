const mongoose = require('mongoose');

const callSchema = new mongoose.Schema({
  conversationId: { type: mongoose.Schema.Types.ObjectId, ref: 'Conversation', required: true },
  caller: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  type: { type: String, enum: ['audio', 'video'], default: 'audio' },
  status: { type: String, enum: ['ongoing', 'completed', 'missed'], default: 'ongoing' },
  startTime: { type: Date, default: Date.now },
  endTime: { type: Date }
}, { timestamps: true });

module.exports = mongoose.model('Call', callSchema);
