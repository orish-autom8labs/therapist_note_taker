const { test, expect } = require('@playwright/test');
const { waitForElement, takeScreenshot, elementExists, getText, formatTestResult } = require('./test-helpers');
const fs = require('fs');
const path = require('path');

test.describe('Active Session Flow', () => {
  test.beforeEach(async ({ page, context }) => {
    // Mock OAuth and start session
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'mock_access_token');
      localStorage.setItem('refresh_token', 'mock_refresh_token');
      localStorage.setItem('user_email', 'test@example.com');
    });
    await page.reload();
    
    // Navigate to session setup and start
    await waitForElement(page, 'input[type="text"]', 10000);
    await page.fill('input[type="text"]', 'Test Patient');
    await page.click('button:has-text("Start"), button:has-text("Begin")');
  });

  test('TS3.1: Recording indicator appears', async ({ page }) => {
    const testName = 'TS3.1: Recording indicator appears';
    const details = {};

    try {
      // Wait for recording indicator (red dot or "Recording..." text)
      await waitForElement(page, 'text=Recording, [data-testid="recording-indicator"], .recording-indicator', 15000);
      details.recording_indicator_found = true;

      // Check for visual indicator (red dot)
      const hasRedDot = await elementExists(page, '[style*="background"][style*="red"], [style*="#E74C3C"]');
      details.red_dot_found = hasRedDot;

      // Take screenshot
      await takeScreenshot(page, 'recording-indicator');
      details.screenshot = 'recording-indicator';

      expect(hasRedDot || details.recording_indicator_found).toBe(true);

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

  test('TS3.2: Patient info card displays correctly', async ({ page }) => {
    const testName = 'TS3.2: Patient info card displays correctly';
    const details = {};

    try {
      // Wait for patient info card
      await waitForElement(page, 'text=Patient, text=Test Patient', 10000);
      details.patient_info_found = true;

      // Check for patient name
      const patientNameText = await getText(page, 'text=Test Patient');
      details.patient_name_displayed = !!patientNameText;

      // Check for start time
      const hasStartTime = await elementExists(page, 'text=Started, text=:');
      details.start_time_found = hasStartTime;

      // Take screenshot
      await takeScreenshot(page, 'patient-info-card');
      details.screenshot = 'patient-info-card';

      expect(details.patient_name_displayed).toBe(true);

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

  test('TS3.3: Transcript area is visible and RTL', async ({ page }) => {
    const testName = 'TS3.3: Transcript area is visible and RTL';
    const details = {};

    try {
      // Wait for transcript area
      await waitForElement(page, 'text=Waiting for speech, [dir="rtl"]', 10000);
      details.transcript_area_found = true;

      // Check RTL direction
      const transcriptArea = await page.locator('[dir="rtl"], [style*="direction: rtl"]').first();
      const direction = await transcriptArea.evaluate(el => {
        return window.getComputedStyle(el).direction;
      });
      details.rtl_direction = direction === 'rtl';

      // Check text alignment
      const textAlign = await transcriptArea.evaluate(el => {
        return window.getComputedStyle(el).textAlign;
      });
      details.text_align = textAlign;

      // Take screenshot
      await takeScreenshot(page, 'transcript-area-rtl');
      details.screenshot = 'transcript-area-rtl';

      expect(details.rtl_direction).toBe(true);

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

  test('TS3.4: Stop & Save button is visible and clickable', async ({ page }) => {
    const testName = 'TS3.4: Stop & Save button is visible and clickable';
    const details = {};

    try {
      // Wait for Stop button
      const stopButton = await page.waitForSelector('button:has-text("Stop"), button:has-text("Save")', { timeout: 10000 });
      details.button_found = true;

      // Check if enabled
      const isEnabled = await stopButton.isEnabled();
      details.button_enabled = isEnabled;

      // Check button styling
      const buttonStyle = await stopButton.evaluate(el => {
        return {
          display: window.getComputedStyle(el).display,
          visibility: window.getComputedStyle(el).visibility,
        };
      });
      details.button_style = buttonStyle;

      // Take screenshot
      await takeScreenshot(page, 'stop-save-button');
      details.screenshot = 'stop-save-button';

      expect(isEnabled).toBe(true);
      expect(buttonStyle.display).not.toBe('none');

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




