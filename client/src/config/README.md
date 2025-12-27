# Session Configuration

This directory contains centralized configuration for the Note Taker application.

## sessionConfig.js

Controls session timing and behavior.

### Quick Start

**For Testing (30 seconds):**
```javascript
maxDuration: 30 * 1000
```

**For Production (60 minutes):**
```javascript
maxDuration: 60 * 60 * 1000
```

### Configuration Options

- **maxDuration**: Maximum session duration in milliseconds
  - Default production: `60 * 60 * 1000` (60 minutes)
  - Testing: `30 * 1000` (30 seconds)

- **autoSaveInterval**: How often to auto-save to Drive (in milliseconds)
  - Default: `60 * 1000` (1 minute)

- **warningThreshold**: When to show warning banner (as fraction of maxDuration)
  - Default: `2/3` (warning at 40 minutes for 60min session, 20s for 30s session)

- **criticalThreshold**: When to show critical warning (as fraction of maxDuration)
  - Default: `5/6` (critical at 50 minutes for 60min session, 25s for 30s session)

### Examples

**Quick 30-second test session:**
```javascript
const sessionConfig = {
  maxDuration: 30 * 1000,        // 30 seconds
  autoSaveInterval: 60 * 1000,   // 1 minute (won't trigger in 30s)
  warningThreshold: 2/3,          // Warning at 20s
  criticalThreshold: 5/6,         // Critical at 25s
};
```

**Custom 2-hour session:**
```javascript
const sessionConfig = {
  maxDuration: 2 * 60 * 60 * 1000,  // 2 hours
  autoSaveInterval: 60 * 1000,       // 1 minute
  warningThreshold: 2/3,              // Warning at 80 minutes
  criticalThreshold: 5/6,             // Critical at 100 minutes
};
```

### User-Configurable Sessions (Future)

To allow users to set their own max duration, you would:

1. Add a settings UI component
2. Store user preference in localStorage or backend
3. Pass the preference to components via props or context
4. Override `sessionConfig.maxDuration` with user preference

Example:
```javascript
// In App.js or Settings component
const userMaxDuration = localStorage.getItem('userMaxDuration') || sessionConfig.maxDuration;

// Pass to ActiveSession
<ActiveSession maxDuration={userMaxDuration} ... />
```
