import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
    errors: ['rate<0.1'],              // Custom error rate must be below 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Test data
const testUsers = [];
for (let i = 0; i < 50; i++) {
  testUsers.push({
    name: `LoadTest User ${i}`,
    email: `loadtest${i}@example.com`,
    password: 'loadtest123',
  });
}

export function setup() {
  // Setup phase - create test data
  console.log('Setting up load test...');
  
  // Register a few test users
  const setupUsers = [];
  for (let i = 0; i < 5; i++) {
    const user = testUsers[i];
    const response = http.post(`${BASE_URL}/auth/register`, JSON.stringify(user), {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (response.status === 200) {
      const tokens = response.json();
      setupUsers.push({
        ...user,
        tokens: tokens,
      });
    }
  }
  
  return { users: setupUsers };
}

export default function (data) {
  // Main test scenarios
  const scenarios = [
    healthCheck,
    authenticationFlow,
    personaOperations,
    aiInteractions,
  ];
  
  // Randomly select a scenario
  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  scenario(data);
  
  sleep(1);
}

function healthCheck() {
  const response = http.get(`${BASE_URL}/health`);
  
  const success = check(response, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
    'health check returns healthy status': (r) => {
      try {
        return r.json().status === 'healthy';
      } catch {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
}

function authenticationFlow() {
  // User registration
  const userIndex = Math.floor(Math.random() * testUsers.length);
  const user = {
    ...testUsers[userIndex],
    email: `loadtest${userIndex}_${Date.now()}@example.com`,
  };
  
  const registerResponse = http.post(
    `${BASE_URL}/auth/register`,
    JSON.stringify(user),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  const registerSuccess = check(registerResponse, {
    'registration status is 200': (r) => r.status === 200,
    'registration response time < 2s': (r) => r.timings.duration < 2000,
    'registration returns tokens': (r) => {
      try {
        const data = r.json();
        return data.access_token && data.refresh_token;
      } catch {
        return false;
      }
    },
  });
  
  if (!registerSuccess) {
    errorRate.add(true);
    return;
  }
  
  const tokens = registerResponse.json();
  
  // User login
  const loginResponse = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ email: user.email, password: user.password }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  const loginSuccess = check(loginResponse, {
    'login status is 200': (r) => r.status === 200,
    'login response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  // Get user profile
  const profileResponse = http.get(`${BASE_URL}/users/me`, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  
  const profileSuccess = check(profileResponse, {
    'profile status is 200': (r) => r.status === 200,
    'profile response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  errorRate.add(!(registerSuccess && loginSuccess && profileSuccess));
}

function personaOperations(data) {
  if (!data.users || data.users.length === 0) {
    return;
  }
  
  const user = data.users[Math.floor(Math.random() * data.users.length)];
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${user.tokens.access_token}`,
  };
  
  // Create persona
  const personaData = {
    name: `Load Test Persona ${Date.now()}`,
    description: 'A persona created during load testing',
    tone: { style: 'friendly' },
    rules: { guidelines: ['Be helpful'] },
    sample_prompts: ['Hello!'],
    safety_rules: ['Keep it appropriate'],
  };
  
  const createResponse = http.post(
    `${BASE_URL}/personas`,
    JSON.stringify(personaData),
    { headers }
  );
  
  const createSuccess = check(createResponse, {
    'persona creation status is 200': (r) => r.status === 200,
    'persona creation response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  if (!createSuccess) {
    errorRate.add(true);
    return;
  }
  
  const persona = createResponse.json();
  
  // Get persona
  const getResponse = http.get(`${BASE_URL}/personas/${persona.persona_id}`, {
    headers,
  });
  
  const getSuccess = check(getResponse, {
    'persona get status is 200': (r) => r.status === 200,
    'persona get response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  // List personas
  const listResponse = http.get(`${BASE_URL}/personas`, { headers });
  
  const listSuccess = check(listResponse, {
    'persona list status is 200': (r) => r.status === 200,
    'persona list response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  errorRate.add(!(createSuccess && getSuccess && listSuccess));
}

function aiInteractions(data) {
  if (!data.users || data.users.length === 0) {
    return;
  }
  
  const user = data.users[Math.floor(Math.random() * data.users.length)];
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${user.tokens.access_token}`,
  };
  
  // Create a persona first
  const personaData = {
    name: `AI Test Persona ${Date.now()}`,
    description: 'A persona for AI testing',
    tone: {},
    rules: {},
    sample_prompts: [],
    safety_rules: [],
  };
  
  const personaResponse = http.post(
    `${BASE_URL}/personas`,
    JSON.stringify(personaData),
    { headers }
  );
  
  if (personaResponse.status !== 200) {
    errorRate.add(true);
    return;
  }
  
  const persona = personaResponse.json();
  
  // AI interaction
  const aiRequest = {
    persona_id: persona.persona_id,
    session_id: `load_test_session_${Date.now()}`,
    user_message: 'Hello, this is a load test message. Can you help me?',
    context: {},
  };
  
  const aiResponse = http.post(
    `${BASE_URL}/ai/respond`,
    JSON.stringify(aiRequest),
    { headers }
  );
  
  const aiSuccess = check(aiResponse, {
    'AI response status is 200': (r) => r.status === 200,
    'AI response time < 5s': (r) => r.timings.duration < 5000,
    'AI response contains text': (r) => {
      try {
        const data = r.json();
        return data.response_text && data.response_text.length > 0;
      } catch {
        return false;
      }
    },
  });
  
  // Get 3D model
  const modelResponse = http.get(
    `${BASE_URL}/3d/persona/${persona.persona_id}`,
    { headers }
  );
  
  const modelSuccess = check(modelResponse, {
    '3D model status is 200': (r) => r.status === 200,
    '3D model response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!(aiSuccess && modelSuccess));
}

export function teardown(data) {
  // Cleanup phase
  console.log('Cleaning up load test...');
  // Add any cleanup logic here if needed
}

export function handleSummary(data) {
  return {
    'performance-results.json': JSON.stringify(data, null, 2),
    stdout: `
Load Test Summary:
==================
Duration: ${data.state.testRunDurationMs}ms
VUs: ${data.metrics.vus.values.max}
Requests: ${data.metrics.http_reqs.values.count}
Request Rate: ${data.metrics.http_req_rate.values.rate}/s
Average Response Time: ${data.metrics.http_req_duration.values.avg}ms
95th Percentile: ${data.metrics.http_req_duration.values['p(95)']}ms
Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
`,
  };
}