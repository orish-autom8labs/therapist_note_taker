# Temporary API Keys Explained

## The Problem: Why Not Use Your Main API Key Directly?

### Scenario 1: Using Main API Key in Browser (❌ BAD)

```javascript
// In your React app (client-side code)
const sonioxClient = new SonioxClient({
  apiKey: "sk_1234567890abcdef..." // Your main API key
});
```

**Problem**: Anyone can:
1. Open browser DevTools
2. View your JavaScript code
3. See your API key
4. **Steal it and use it for their own purposes**
5. **Run up your bill** or access your account

**This is a security risk!** 🔴

---

## The Solution: Temporary API Keys (✅ GOOD)

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│ 1. Your Server (Secure)                                  │
│    - Has your MAIN API key (never exposed)                │
│    - Calls Soniox API to generate temporary key           │
│    - Returns temporary key to client                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Client (Browser)                                       │
│    - Gets temporary key from your server                  │
│    - Uses temporary key to connect to Soniox              │
│    - Temporary key expires in 60 seconds                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Soniox API                                            │
│    - Validates temporary key                              │
│    - Allows transcription only                            │
│    - Key expires automatically                            │
└─────────────────────────────────────────────────────────┘
```

---

## How Temporary Keys Are Generated

### Step-by-Step Process

1. **Client requests temporary key**:
   ```javascript
   // Client (browser) calls your server
   const response = await fetch('http://localhost:3001/v1/auth/temporary-api-key', {
     method: 'POST'
   });
   const { apiKey } = await response.json();
   ```

2. **Your server generates temporary key**:
   ```python
   # Your server (secure, has your main API key)
   async def generate_temporary_api_key():
       # Use YOUR main API key to call Soniox
       response = await httpx.post(
           "https://api.soniox.com/v1/auth/temporary-api-key",
           headers={
               "Authorization": f"Bearer {YOUR_MAIN_API_KEY}"  # Your real key
           },
           json={
               "usage_type": "transcribe_websocket",
               "expires_in_seconds": 60  # Expires in 60 seconds
           }
       )
       return response.json()["api_key"]  # Return temporary key
   ```

3. **Soniox returns temporary key**:
   ```json
   {
     "api_key": "temp:WYJ67RBEFUWQXXPKYPD2UGXKWB",
     "expires_at": "2025-02-22T22:47:37.150Z"
   }
   ```

4. **Client uses temporary key**:
   ```javascript
   // Client uses temporary key (safe to expose)
   const sonioxClient = new SonioxClient({
     apiKey: "temp:WYJ67RBEFUWQXXPKYPD2UGXKWB"  // Temporary, expires soon
   });
   ```

---

## Why This Is Secure

### ✅ Benefits

1. **Main API key never exposed**: Stays on your server
2. **Limited scope**: Temporary key can only do specific things (e.g., transcription)
3. **Short expiry**: Expires in 60 seconds (or whatever you set)
4. **Even if stolen**: Someone can't do much with a key that expires in 60 seconds
5. **Usage tracking**: You can track who uses temporary keys

### 🔒 Security Comparison

| Approach | Main API Key Exposed? | Risk Level |
|----------|----------------------|-----------|
| **Use main key directly** | ✅ YES (in browser code) | 🔴 HIGH |
| **Use temporary keys** | ❌ NO (only on server) | 🟢 LOW |

---

## Can We Skip Temporary Keys?

### Option 1: Use Main API Key Directly (Not Recommended)

**Technically possible**, but:
- ❌ Security risk (key exposed in browser)
- ❌ Anyone can steal it
- ❌ Can be used for anything (not just transcription)
- ❌ No expiration
- ❌ Violates security best practices

**Only use this for**: Testing, development, or if you don't care about security.

### Option 2: Use Temporary Keys (Recommended)

**Best practice**:
- ✅ Main key stays secure on server
- ✅ Temporary keys expire quickly
- ✅ Limited scope (only transcription)
- ✅ Industry standard approach
- ✅ What Soniox recommends

---

## How It Works in the Official Example

Looking at the official Soniox example:

### Server Code (Your Server)
```python
# server/main.py
@app.post("/v1/auth/temporary-api-key")
async def generate_temporary_api_key():
    # Your server has YOUR main API key (from environment variable)
    soniox_api_key = os.getenv("SONIOX_API_KEY")  # Your real key
    
    # Call Soniox API to generate temporary key
    response = await httpx.post(
        "https://api.soniox.com/v1/auth/temporary-api-key",
        headers={
            "Authorization": f"Bearer {soniox_api_key}"  # Use your real key
        },
        json={
            "usage_type": "transcribe_websocket",
            "expires_in_seconds": 60
        }
    )
    
    # Return temporary key to client
    return {"apiKey": response.json()["api_key"]}
```

### Client Code (Browser)
```typescript
// client/src/utils/get-api-key.ts
export default async function getAPIKey() {
  // Request temporary key from YOUR server
  const response = await fetch(
    "http://localhost:8000/v1/auth/temporary-api-key",
    { method: "POST" }
  );
  const { apiKey } = await response.json();
  return apiKey;  // Temporary key (safe to use in browser)
}
```

---

## For Your Note-Taker App

### Current Architecture (Server-Proxied)
- ✅ Main API key on server (secure)
- ✅ Client never sees API key
- ✅ Server handles all Soniox communication

### New Architecture (SDK-Based)
- ✅ Main API key on server (secure)
- ✅ Server generates temporary keys
- ✅ Client uses temporary keys (safe to expose)
- ✅ Temporary keys expire in 60 seconds

**Both are secure**, but SDK approach:
- Fixes timeout issues
- Simplifies architecture
- Uses industry best practices

---

## Summary

**Temporary API keys are**:
- Generated by **your server** using **your main API key**
- Returned to the **client** for use
- **Limited scope** (only transcription)
- **Short-lived** (expire in 60 seconds)
- **Safe to expose** in browser code

**Why use them**:
- 🔒 **Security**: Main API key never exposed
- 🛡️ **Protection**: Even if stolen, expires quickly
- ✅ **Best practice**: Industry standard approach
- 📚 **Recommended**: What Soniox documentation suggests

**Can you use main API key directly?**
- Technically yes, but **not recommended**
- Security risk (key exposed in browser)
- Violates best practices

---

## Questions?

**Q: Do I need to change my main API key?**  
A: No, you keep using the same main API key. It stays on your server.

**Q: How often are temporary keys generated?**  
A: Every time the client needs one (usually when starting a session).

**Q: What happens when a temporary key expires?**  
A: The client requests a new one from your server.

**Q: Can I use my main API key directly if I don't care about security?**  
A: Yes, but it's not recommended. For production, always use temporary keys.

