/**
 * Test helpers for Note Taker browser automation tests
 * These functions help with common test operations
 */

/**
 * Wait for element to be visible
 */
async function waitForElement(page, selector, timeout = 5000) {
  await page.waitForSelector(selector, { state: 'visible', timeout });
}

/**
 * Take screenshot with timestamp
 */
async function takeScreenshot(page, name) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({ 
    path: `test-results/screenshots/${name}-${timestamp}.png`,
    fullPage: true 
  });
}

/**
 * Check if element exists and is visible
 */
async function elementExists(page, selector) {
  try {
    await page.waitForSelector(selector, { state: 'visible', timeout: 2000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Get element text content
 */
async function getText(page, selector) {
  const element = await page.waitForSelector(selector);
  return await element.textContent();
}

/**
 * Check console for errors
 */
async function checkConsoleErrors(page) {
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  return errors;
}

/**
 * Wait for WebSocket connection
 */
async function waitForWebSocket(page) {
  await page.waitForFunction(() => {
    return window.WebSocket && document.querySelector('[data-testid="recording-indicator"]');
  }, { timeout: 10000 });
}

/**
 * Format test result for agent reading
 */
function formatTestResult(testName, passed, details = {}) {
  return {
    test_name: testName,
    status: passed ? 'PASS' : 'FAIL',
    timestamp: new Date().toISOString(),
    details: {
      ...details,
      screenshot: details.screenshot || null,
      errors: details.errors || [],
      console_logs: details.console_logs || [],
    }
  };
}

module.exports = {
  waitForElement,
  takeScreenshot,
  elementExists,
  getText,
  checkConsoleErrors,
  waitForWebSocket,
  formatTestResult,
};




