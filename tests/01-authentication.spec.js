const { test, expect } = require('@playwright/test');
const { waitForElement, takeScreenshot, elementExists, formatTestResult } = require('./test-helpers');
const fs = require('fs');
const path = require('path');

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto('/');
  });

  test('TS1.1: Login screen displays correctly', async ({ page }) => {
    const testName = 'TS1.1: Login screen displays correctly';
    const details = {};

    try {
      // Check for login screen elements
      await waitForElement(page, 'button:has-text("Sign in with Google")', 10000);
      details.login_button_found = true;

      // Check for app title
      const titleExists = await elementExists(page, 'h1, h2');
      details.title_found = titleExists;

      // Take screenshot
      await takeScreenshot(page, 'login-screen');
      details.screenshot = 'login-screen';

      // Verify page loaded
      await expect(page).toHaveTitle(/Note Taker|note taker/i);

      const result = formatTestResult(testName, true, details);
      fs.writeFileSync(
        path.join(__dirname, 'test-results', `${testName.replace(/[^a-zA-Z0-9]/g, '_')}.json`),
        JSON.stringify(result, null, 2)
      );

    } catch (error) {
      const result = formatTestResult(testName, false, {
        ...details,
        error: error.message,
        stack: error.stack
      });
      fs.writeFileSync(
        path.join(__dirname, 'test-results', `${testName.replace(/[^a-zA-Z0-9]/g, '_')}.json`),
        JSON.stringify(result, null, 2)
      );
      throw error;
    }
  });

  test('TS1.2: Google sign-in button is clickable', async ({ page }) => {
    const testName = 'TS1.2: Google sign-in button is clickable';
    const details = {};

    try {
      // Find and verify button
      const signInButton = await page.waitForSelector('button:has-text("Sign in with Google")', { timeout: 10000 });
      details.button_found = true;

      // Check if button is enabled
      const isEnabled = await signInButton.isEnabled();
      details.button_enabled = isEnabled;

      // Check button styling
      const buttonStyle = await signInButton.evaluate(el => {
        return {
          display: window.getComputedStyle(el).display,
          visibility: window.getComputedStyle(el).visibility,
          pointerEvents: window.getComputedStyle(el).pointerEvents,
        };
      });
      details.button_style = buttonStyle;

      // Take screenshot
      await takeScreenshot(page, 'sign-in-button');
      details.screenshot = 'sign-in-button';

      expect(isEnabled).toBe(true);
      expect(buttonStyle.display).not.toBe('none');
      expect(buttonStyle.visibility).toBe('visible');

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




