const Client = require('socket.io-client');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');

// Mock Firebase Admin Auth
jest.mock('firebase-admin', () => ({
  initializeApp: jest.fn(),
  credential: { cert: jest.fn() }
}));

jest.mock('firebase-admin/auth', () => ({
  getAuth: () => ({
    verifyIdToken: jest.fn(async (token) => {
      if (token === 'valid_test_token') {
        return { uid: 'user_1', email: 'test@example.com', name: 'TestUser' };
      }
      throw new Error('Invalid token');
    })
  })
}));

let mongoServer;
let app, server, io, User, Conversation, Message;
let clientSocket;
let conversationId;
let userId;

beforeAll(async () => {
  mongoServer = await MongoMemoryServer.create();
  process.env.MONGO_URI = mongoServer.getUri();
  
  const serverModule = require('../server');
  app = serverModule.app;
  server = serverModule.server;
  io = serverModule.io;
  
  User = require('../models/User');
  Conversation = require('../models/Conversation');
  Message = require('../models/Message');

  // Start the server on an ephemeral port
  await new Promise((resolve) => {
    server.listen(0, resolve);
  });

  // Seed DB with a conversation so the socket has something to join
  const user = await User.create({ uid: 'user_1', email: 'test@example.com', displayName: 'TestUser' });
  userId = user._id;
  const conv = await Conversation.create({ participants: [user._id] });
  conversationId = conv._id.toString();

  // Create test socket
  const port = server.address().port;
  clientSocket = new Client(`http://localhost:${port}`, {
    auth: { token: 'valid_test_token' }
  });

  await new Promise((resolve) => {
    clientSocket.on('connect', resolve);
  });
});

afterAll(async () => {
  clientSocket.close();
  if (io) io.close();
  if (server) server.close();
  await mongoose.disconnect();
  await mongoServer.stop();
});

describe('Socket.io Server', () => {
  it('should fetch empty history successfully', (done) => {
    clientSocket.emit('getHistory', { conversationId });
    
    clientSocket.once('history', (data) => {
      expect(data.conversationId).toBe(conversationId);
      expect(Array.isArray(data.messages)).toBe(true);
      expect(data.messages.length).toBe(0);
      done();
    });
  });

  it('should broadcast message to room and save it to DB', (done) => {
    const testMessageId = 'test_msg_id_1';
    
    clientSocket.emit('sendMessage', {
      id: testMessageId,
      conversationId,
      text: 'Hello DB!',
    });

    clientSocket.once('newMessage', async (msg) => {
      expect(msg.text).toBe('Hello DB!');
      expect(msg.id).toBe(testMessageId);
      expect(msg.senderId._id.toString()).toBe(userId.toString());
      
      // Verify DB persistence
      const dbMessage = await Message.findOne({ id: testMessageId });
      expect(dbMessage).not.toBeNull();
      expect(dbMessage.text).toBe('Hello DB!');
      done();
    });
  });

  it('should mark message as read', async () => {
    const testMessageId = 'test_msg_id_2';
    
    // Create an unread message first
    await Message.create({
      id: testMessageId,
      conversationId,
      senderId: userId,
      text: 'Unread message',
      readBy: []
    });
    
    return new Promise((resolve) => {
      clientSocket.emit('markAsRead', { messageId: testMessageId });

      clientSocket.once('messageRead', async ({ messageId, readBy }) => {
        expect(messageId).toBe(testMessageId);
        expect(readBy.map(id => id.toString())).toContain(userId.toString());
        resolve();
      });
    });
  });
});
