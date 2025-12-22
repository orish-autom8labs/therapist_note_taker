const { test, expect } = require('@playwright/test');
const { waitForElement, takeScreenshot, elementExists, getText, formatTestResult } = require('./test-helpers');
const fs = require('fs');
const path = require('path');

test.describe('Session Setup Flow', () => {
  test.beforeEach(async ({ page, context }) => {
    // Mock OAuth - set tokens in localStorage
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'mock_access_token');
      localStorage.setItem('refresh_token', 'mock_refresh_token');
      localStorage.setItem('user_email', 'test@example.com');
    });
    await page.reload();
  });

  test('TS2.1: Session setup screen displays after login', async ({ page }) => {
    const testName = 'TS2.1: Session setup screen displays after login';
    const details = {};

    try {
      // Wait for session setup screen
      await waitForElement(page, 'input[type="text"], input[placeholder*="patient" i], input[placeholder*="name" i]', 10000);
      details.patient_input_found = true;

      // Check for Start button
      const startButtonExists = await elementExists(page, 'button:has-text("Start"), button:has-text("Begin")');
      details.start_button_found = startButtonExists;

      // Check for Back link
      const backLinkExists = await elementExists(page, 'a:has-text("Back"), a:has-text("←")');
      details.back_link_found = backLinkExists;

      // Take screenshot
      await takeScreenshot(page, 'session-setup-screen');
      details.screenshot = 'session-setup-screen';

      expect(startButtonExists).toBe(true);

      const result = formatTestResult(testName, true, details);
      fs.writeFileSync(
        path.join(__dirname, 'test-results', `${testName.replace(/[^a-zA-Z0-9]/g, '_')}.json`),
        JSON.stringify(result, null, 2)
      );

    } catch (error) {
      const result = formatTestResult(testName, false, {
        ...details,
        error: error.message
      });
      fs.writeFileSync(
        path.join(__dirname, 'test-results', `${testName.replace(/[^a-zA-Z0-9]/g, '_')}.json`),
        JSON.stringify(result, null, 2)
      );
      throw error;
    }
  });

  test('TS2.2: Patient name input accepts text', async ({ page }) => {
    const testName = 'TS2.2: Patient name input accepts text';
    const details = {};

    try {
      // Find input field
      const input = await page.waitForSelector('input[type="text"], input[placeholder*="patient" i]', { timeout: 10000 });
      details.input_found = true;

      // Type patient name
      const testName = 'Test Patient';
      await input.fill(testName);
      details.input_value = testName;

      // Verify value
      const value = await input.inputValue();
      details.actual_value = value;

      // Take screenshot
      await takeScreenshot(page, 'patient-name-input');
      details.screenshot = 'patient-name-input';

      expect(value).toBe(testName);

      const result = formatTestResult(testName, true, details);
      fs.writeFileSync(
        path.join(__dirname, 'test-results', `${testName.replace(/[^a-zA-Z0-9]/g, '_')}.json`),
        JSON.stringify(result, null, 2)
      );

    } catch (error) {
      const result = formatTestResult(testName, false, {
        ...details,
        error: error.message
      });
      fs.writeFileSync(
        path.join(__dirname, 'test-results', `${testName.replace(/[^a-zA-Z0-9]/g, '_')}.json`),
        JSON.stringify(result, null, 2)
      );
      throw error;
    }
  });

  test('TS2.3: Start button enables after entering patient name', async ({ page }) => {
    const testName = 'TS2.3: Start button enables after entering patient name';
    const details = {};

    try {
      // Enter patient name
      const input = await page.waitForSelector('input[type="text"], input[placeholder*="patient" i]', { timeout: 10000 });
      await input.fill('Test Patient');

      // Find Start button
      const startButton = await page.waitForSelector('button:has-text("Start"), button:has-text("Begin")', { timeout: 5000 });
      details.button_found = true;

      // Check if enabled
      const isEnabled = await startButton.isEnabled();
      details.button_enabled = isEnabled;

      // Take screenshot
      await takeScreenshot(page, 'start-button-enabled');
      details.screenshot = 'start-button-enabled';

      expect(isEnabled).toBe(true);

      const result = formatTestResult(testName, true, details);
      fs.writeFileSync(
        path.join(__dirname, 'test-results', `${testName.replace(/[^a-zA-Z0-9]/g, '_')}.json`),
        JSON.stringify(result, null, 2)
      );

    } catch (error) {
      const result = formatTestResult(testName, false, {
        ...details,
        error: error.message
      });
      fs.writeFileSync(
        path.join(__dirname, 'test-results', `${testName.replace(/[^a-zA-Z0-9]/g, '_')}.json`),
        JSON.stringify(result, null, 2)
      );
      throw error;
    }
  });
});




