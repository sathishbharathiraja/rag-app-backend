const autocannon = require('autocannon');

const url = 'http://localhost:3001';

// We just hit the main endpoint which serves the React index.html
// as a simple way to test connection limits and raw throughput.
const instance = autocannon({
  url: url,
  connections: 100, // Simulate 100 concurrent users
  pipelining: 10,   // High pipelining
  duration: 10,     // 10 seconds test
}, console.log);

autocannon.track(instance, { renderProgressBar: true });

console.log(`Running stress test against ${url} for 10 seconds with 100 concurrent users...`);
console.log('Ensure you have "npm start" running in another terminal!');
