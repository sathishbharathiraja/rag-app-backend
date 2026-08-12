const admin = require('firebase-admin');
const { getAuth } = require('firebase-admin/auth');

try {
  const app = admin.initializeApp({ projectId: 'realtime-chat-86476' });
  console.log('Initialized');
  
  const auth = getAuth(app);
  console.log('Auth initialized');
} catch (e) {
  console.error(e);
}
