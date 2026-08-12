const request = require('supertest');
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
      if (token === 'valid_token_user1') return { uid: 'user1_uid', email: 'user1@example.com', name: 'User One' };
      if (token === 'valid_token_user2') return { uid: 'user2_uid', email: 'user2@example.com', name: 'User Two' };
      throw new Error('Invalid token');
    })
  })
}));

let mongoServer;
let app, server, io, User, Conversation;

beforeAll(async () => {
  // Start MongoMemoryServer and set URI BEFORE requiring server.js
  mongoServer = await MongoMemoryServer.create();
  process.env.MONGO_URI = mongoServer.getUri();
  
  const serverModule = require('../server');
  app = serverModule.app;
  server = serverModule.server;
  io = serverModule.io;
  
  User = require('../models/User');
  Conversation = require('../models/Conversation');
});

afterAll(async () => {
  await mongoose.disconnect();
  await mongoServer.stop();
  if (server) server.close();
});

beforeEach(async () => {
  await User.deleteMany({});
  await Conversation.deleteMany({});
});

describe('API Routes', () => {
  describe('GET /api/users/search', () => {
    it('returns 401 without auth token', async () => {
      const res = await request(app).get('/api/users/search?email=test');
      expect(res.status).toBe(401);
    });

    it('returns empty array if no email query', async () => {
      // First create the caller user in DB
      await User.create({ uid: 'user1_uid', email: 'user1@example.com', displayName: 'User One' });

      const res = await request(app)
        .get('/api/users/search')
        .set('Authorization', 'Bearer valid_token_user1');
      
      expect(res.status).toBe(200);
      expect(res.body).toEqual([]);
    });

    it('returns matching users excluding the caller', async () => {
      const caller = await User.create({ uid: 'user1_uid', email: 'user1@example.com', displayName: 'User One' });
      await User.create({ uid: 'user2_uid', email: 'user2@example.com', displayName: 'User Two' });
      await User.create({ uid: 'user3_uid', email: 'other@example.com', displayName: 'Other' });

      const res = await request(app)
        .get('/api/users/search?email=user')
        .set('Authorization', 'Bearer valid_token_user1');
      
      expect(res.status).toBe(200);
      expect(res.body).toHaveLength(1);
      expect(res.body[0].email).toBe('user2@example.com');
    });
  });

  describe('POST /api/conversations', () => {
    it('creates a new conversation between two users', async () => {
      const user1 = await User.create({ uid: 'user1_uid', email: 'user1@example.com', displayName: 'User One' });
      const user2 = await User.create({ uid: 'user2_uid', email: 'user2@example.com', displayName: 'User Two' });

      const res = await request(app)
        .post('/api/conversations')
        .set('Authorization', 'Bearer valid_token_user1')
        .send({ targetUserId: user2._id });

      expect(res.status).toBe(200);
      expect(res.body.participants).toHaveLength(2);
      expect(res.body.isGroup).toBe(false);
    });

    it('returns existing conversation if one already exists', async () => {
      const user1 = await User.create({ uid: 'user1_uid', email: 'user1@example.com', displayName: 'User One' });
      const user2 = await User.create({ uid: 'user2_uid', email: 'user2@example.com', displayName: 'User Two' });

      await Conversation.create({ participants: [user1._id, user2._id] });

      const res = await request(app)
        .post('/api/conversations')
        .set('Authorization', 'Bearer valid_token_user1')
        .send({ targetUserId: user2._id });

      expect(res.status).toBe(200);
      expect(res.body.participants).toHaveLength(2);
    });
  });
});
