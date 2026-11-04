import { defineConfig, devices } from '@playwright/test';
import { resolve } from 'node:path';

const python = process.platform === 'win32' ? '..\\.venv\\Scripts\\python.exe' : '../.venv/bin/python';
const visionPython = process.platform === 'win32' ? '..\\services\\vision\\.venv\\Scripts\\python.exe' : '../services/vision/.venv/bin/python';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  use: { baseURL: 'http://localhost:5174', trace: 'retain-on-failure' },
  webServer: [
    {
      command: `${visionPython} -m uvicorn app.main:app --app-dir ../services/vision --host 127.0.0.1 --port 8003`,
      url: 'http://127.0.0.1:8003/health',
      env: { VISION_API_KEY: 'e2e-internal-only', VISION_DATA_DIR: resolve('../tmp/e2e-vision') },
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: `${python} ../backend/manage.py migrate --settings=config.e2e && ${python} ../backend/manage.py prepare_e2e --settings=config.e2e && ${python} ../backend/manage.py run_e2e_server --settings=config.e2e`,
      url: 'http://127.0.0.1:8001/api/auth/csrf/',
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: 'npm run dev -- --port 5174',
      url: 'http://127.0.0.1:5174',
      env: { API_PROXY_TARGET: 'http://127.0.0.1:8001' },
      reuseExistingServer: false,
      timeout: 60000,
    },
  ],
  projects: process.env.E2E_BROWSER === 'edge'
    ? [{ name: 'edge', use: { ...devices['Desktop Edge'], channel: 'msedge' } }]
    : [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  reporter: 'list',
});
