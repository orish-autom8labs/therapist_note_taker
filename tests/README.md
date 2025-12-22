# Browser Automation Tests for Note Taker

This directory contains browser automation tests using Playwright that can be executed by an AI agent to validate the UI, functionality, and user experience.

## Test Capabilities

These tests can:
- ✅ Open and control a browser (Chrome, Firefox, Safari)
- ✅ Navigate to pages and interact with elements
- ✅ Click buttons, fill forms, verify UI elements
- ✅ Capture screenshots for visual verification
- ✅ Check console logs, network requests, DOM state
- ✅ Validate text content, styling, and layout
- ✅ Generate agent-readable JSON results

## Setup

1. **Install dependencies**:
   ```bash
   cd tests
   npm install
   ```

2. **Install Playwright browsers**:
   ```bash
   npx playwright install chromium
   ```

3. **Start the app** (in separate terminals):
   ```bash
   # Terminal 1: Backend
   cd server
   python run.py

   # Terminal 2: Frontend
   cd client
   npm start
   ```

## Running Tests

### Run all tests:
```bash
npm test
```

### Run with UI (interactive):
```bash
npm run test:ui
```

### Run in headed mode (see browser):
```bash
npm run test:headed
```

### Run in debug mode:
```bash
npm run test:debug
```

### View test report:
```bash
npm run test:report
```

## Test Structure

### Test Files:
- `01-authentication.spec.js` - Login and authentication flows
- `02-session-setup.spec.js` - Session creation and setup
- `03-active-session.spec.js` - Active transcription session
- `04-success-screen.spec.js` - Success screen and Drive integration

### Test Results:
- **JSON files**: `test-results/*.json` - Agent-readable results
- **Screenshots**: `test-results/screenshots/*.png` - Visual verification
- **HTML Report**: `test-results/html-report/index.html` - Human-readable report

## Agent-Readable Results Format

Each test generates a JSON file with:
```json
{
  "test_name": "TS1.1: Login screen displays correctly",
  "status": "PASS",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "details": {
    "login_button_found": true,
    "title_found": true,
    "screenshot": "login-screen",
    "errors": [],
    "console_logs": []
  }
}
```

## Test Scenarios Covered

### Authentication (TS1)
- ✅ Login screen displays correctly
- ✅ Google sign-in button is clickable
- ✅ Error handling

### Session Setup (TS2)
- ✅ Session setup screen displays after login
- ✅ Patient name input accepts text
- ✅ Start button enables after entering patient name

### Active Session (TS3)
- ✅ Recording indicator appears
- ✅ Patient info card displays correctly
- ✅ Transcript area is visible and RTL
- ✅ Stop & Save button is visible and clickable

### Success Screen (TS4)
- ✅ Success screen displays after session completion
- ✅ File info displays correctly
- ✅ View in Drive button enabled when link exists
- ✅ View in Drive button disabled when link missing
- ✅ New Session button works

## Adding New Tests

1. Create a new test file: `XX-feature-name.spec.js`
2. Use test helpers from `test-helpers.js`
3. Generate results using `formatTestResult()`
4. Save results to `test-results/` directory

## Troubleshooting

### Tests fail to find elements:
- Check if app is running on `http://localhost:3000`
- Verify selectors match actual UI elements
- Check browser console for errors

### Screenshots not captured:
- Ensure `test-results/screenshots/` directory exists
- Check file permissions

### WebSocket connection issues:
- Verify backend is running on `http://localhost:3001`
- Check WebSocket endpoint configuration




