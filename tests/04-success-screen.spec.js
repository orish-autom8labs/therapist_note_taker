const { test, expect } = require('@playwright/test');
const { waitForElement, takeScreenshot, elementExists, getText, formatTestResult } = require('./test-helpers');
const fs = require('fs');
const path = require('path');

test.describe('Success Screen Flow', () => {
  test('TS4.1: Success screen displays after session completion', async ({ page }) => {
    const testName = 'TS4.1: Success screen displays after session completion';
    const details = {};

    try {
      // Mock completed session by setting fileInfo in localStorage
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('access_token', 'mock_access_token');
        localStorage.setItem('fileInfo', JSON.stringify({
          fileId: 'test_file_id',
          fileName: 'Test_Patient_2024-01-01_12-00.txt',
          webViewLink: 'https://drive.google.com/file/d/test_file_id/view',
        }));
      });
      await page.reload();

      // Wait for success screen elements
      await waitForElement(page, 'text=Session Saved, text=Saved', 10000);
      details.success_message_found = true;

      // Check for checkmark
      const checkmarkExists = await elementExists(page, 'text=✓, [style*="color"][style*="green"]');
      details.checkmark_found = checkmarkExists;

      // Take screenshot
      await takeScreenshot(page, 'success-screen');
      details.screenshot = 'success-screen';

      expect(details.success_message_found).toBe(true);

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

  test('TS4.2: File info displays correctly', async ({ page }) => {
    const testName = 'TS4.2: File info displays correctly';
    const details = {};

    try {
      // Mock fileInfo
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('fileInfo', JSON.stringify({
          fileName: 'Test_Patient_2024-01-01_12-00.txt',
          webViewLink: 'https://drive.google.com/file/d/test/view',
        }));
      });
      await page.reload();

      // Check for file name
      const fileNameExists = await elementExists(page, 'text=Test_Patient_2024-01-01_12-00.txt');
      details.file_name_displayed = fileNameExists;

      // Check for location
      const locationExists = await elementExists(page, 'text=Clinic/Transcripts, text=Location');
      details.location_displayed = locationExists;

      // Take screenshot
      await takeScreenshot(page, 'file-info-display');
      details.screenshot = 'file-info-display';

      expect(fileNameExists).toBe(true);

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

  test('TS4.3: View in Drive button enabled when link exists', async ({ page }) => {
    const testName = 'TS4.3: View in Drive button enabled when link exists';
    const details = {};

    try {
      // Mock fileInfo with webViewLink
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('fileInfo', JSON.stringify({
          fileName: 'test.txt',
          webViewLink: 'https://drive.google.com/file/d/test/view',
        }));
      });
      await page.reload();

      // Wait for View in Drive button
      const viewButton = await page.waitForSelector('button:has-text("View in Drive")', { timeout: 10000 });
      details.button_found = true;

      // Check if enabled
      const isEnabled = await viewButton.isEnabled();
      details.button_enabled = isEnabled;

      // Check button style (should not be disabled)
      const opacity = await viewButton.evaluate(el => {
        return window.getComputedStyle(el).opacity;
      });
      details.button_opacity = opacity;
      details.button_should_be_enabled = parseFloat(opacity) >= 1.0;

      // Take screenshot
      await takeScreenshot(page, 'view-in-drive-button-enabled');
      details.screenshot = 'view-in-drive-button-enabled';

      expect(isEnabled).toBe(true);
      expect(parseFloat(opacity)).toBeGreaterThanOrEqual(1.0);

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

  test('TS4.4: View in Drive button disabled when link missing', async ({ page }) => {
    const testName = 'TS4.4: View in Drive button disabled when link missing';
    const details = {};

    try {
      // Mock fileInfo without webViewLink
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('fileInfo', JSON.stringify({
          fileName: 'test.txt',
          // No webViewLink
        }));
      });
      await page.reload();

      // Wait for View in Drive button
      const viewButton = await page.waitForSelector('button:has-text("View in Drive")', { timeout: 10000 });
      details.button_found = true;

      // Check if disabled
      const isDisabled = await viewButton.isDisabled();
      details.button_disabled = isDisabled;

      // Check button style (should be disabled)
      const opacity = await viewButton.evaluate(el => {
        return window.getComputedStyle(el).opacity;
      });
      const cursor = await viewButton.evaluate(el => {
        return window.getComputedStyle(el).cursor;
      });
      details.button_opacity = opacity;
      details.button_cursor = cursor;
      details.button_should_be_disabled = parseFloat(opacity) < 1.0 || cursor === 'not-allowed';

      // Take screenshot
      await takeScreenshot(page, 'view-in-drive-button-disabled');
      details.screenshot = 'view-in-drive-button-disabled';

      expect(isDisabled || parseFloat(opacity) < 1.0).toBe(true);

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

  test('TS4.5: New Session button works', async ({ page }) => {
    const testName = 'TS4.5: New Session button works';
    const details = {};

    try {
      // Mock fileInfo
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('fileInfo', JSON.stringify({
          fileName: 'test.txt',
        }));
      });
      await page.reload();

      // Find and click New Session button
      const newSessionButton = await page.waitForSelector('button:has-text("New Session")', { timeout: 10000 });
      details.button_found = true;

      await newSessionButton.click();
      details.button_clicked = true;

      // Wait for navigation to session setup
      await waitForElement(page, 'input[type="text"]', 5000);
      details.navigated_to_setup = true;

      // Take screenshot
      await takeScreenshot(page, 'new-session-clicked');
      details.screenshot = 'new-session-clicked';

      expect(details.navigated_to_setup).toBe(true);

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




