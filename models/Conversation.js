const mongoose = require('mongoose');

const conversationSchema = new mongoose.Schema({
  isGroup: { type: Boolean, default: false },
  name: { type: String }, // Optional name for groups
  participants: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
  lastMessage: { type: mongoose.Schema.Types.ObjectId, ref: 'Message' },
  updatedAt: { type: Date, default: Date.now },
  pinBoard: {
    status: { type: String, default: 'On Track' },
    links: [{ title: String, url: String }],
    deadlines: [{ task: String, date: String }]
  }
});

module.exports = mongoose.model('Conversation', conversationSchema);
