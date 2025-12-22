const STORAGE_KEY = 'session_backup';
const MAX_AGE = 3600000; // 1 hour

export function saveToLocalStorage(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      ...data,
      timestamp: Date.now(),
    }));
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
  }
}

export function checkForRecovery() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;

    const data = JSON.parse(stored);
    const age = Date.now() - data.timestamp;

    // Only recover if less than 1 hour old
    if (age < MAX_AGE) {
      return data;
    } else {
      // Clean up old data
      clearRecoveryData();
      return null;
    }
  } catch (error) {
    console.error('Failed to check recovery:', error);
    return null;
  }
}

export function clearRecoveryData() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear recovery data:', error);
  }
}




