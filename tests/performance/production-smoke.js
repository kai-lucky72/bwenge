import http from 'k6/http';
import { check, sleep } from 'k6';

// Lightweight production smoke test
export const options = {
  duration: '2m',
  vus: 10,
  thresholds: {
    http_req_duration: ['p(95)<3000'], // 95% of requests must complete below 3s
    http_req_failed: ['rate<0.05'],    // Error rate must be below 5%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Health check
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check is successful': (r) => r.status === 200,
    'health check response time OK': (r) => r.timings.duration < 1000,
  });
  
  // Basic API availability check
  const registerResponse = http.post(
    `${BASE_URL}/auth/register`,
    JSON.stringify({
      name: 'Smoke Test User',
      email: `smoketest${Date.now()}@example.com`,
      password: 'smoketest123',
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(registerResponse, {
    'registration endpoint available': (r) => r.status === 200,
    'registration response time OK': (r) => r.timings.duration < 2000,
  });
  
  sleep(1);
}