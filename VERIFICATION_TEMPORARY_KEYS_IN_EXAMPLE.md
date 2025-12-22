# Verification: Official Soniox Example Uses Temporary API Keys

## ✅ Confirmed: Yes, the Official Example Uses Temporary API Keys

Let me trace through the code to show you exactly how:

---

## Flow in the Official Example

### Step 1: Client Requests Temporary Key

**File**: `react/src/utils/get-api-key.ts`

```typescript
// Fetch temporary API key from the server, so we can establish websocket connection.
// Read more on: https://soniox.com/docs/speech-to-text/guides/direct-stream#temporary-api-keys
export default async function getAPIKey() {
  const response = await fetch(
    "http://localhost:8000/v1/auth/temporary-api-key",  // ← Calls YOUR server
    {
      method: "POST",
    },
  );
  const { apiKey } = await response.json();
  return apiKey;  // ← Returns temporary key
}
```

**What this does**: Client calls YOUR server to get a temporary key.

---

### Step 2: Client Uses Temporary Key

**File**: `react/src/renderers/transcribe.tsx`

```typescript
import getAPIKey from "@/utils/get-api-key";  // ← Import the function

export default function Transcribe() {
  const {
    state,
    finalTokens,
    nonFinalTokens,
    startTranscription,
    stopTranscription,
    error,
  } = useSonioxClient({
    apiKey: getAPIKey,  // ← Pass the function (not a string!)
  });
```

**What this does**: Passes `getAPIKey` function (not a hardcoded key) to the SDK.

---

### Step 3: SDK Calls the Function to Get Key

**File**: `react/src/hooks/useSonioxClient.tsx`

```typescript
interface UseSonioxClientOptions {
  apiKey: string | (() => Promise<string>);  // ← Can be string OR function
  // ...
}

export default function useSonioxClient({
  apiKey,  // ← This is the getAPIKey function
  // ...
}: UseSonioxClientOptions) {
  const sonioxClient = useRef<SonioxClient | null>(null);

  if (sonioxClient.current == null) {
    sonioxClient.current = new SonioxClient({
      apiKey: apiKey,  // ← SDK will call this function when needed
    });
  }
```

**What this does**: SDK receives the function and calls it when it needs the API key.

---

### Step 4: Server Generates Temporary Key

**File**: `server/main.py`

```python
@app.post("/v1/auth/temporary-api-key")
async def generate_temporary_api_key():
    """
    Generate a temporary API key for Soniox WebSocket transcription.
    
    You don't want to expose the API key to the client, so we generate a temporary one.
    Temporary API keys are then used to initialize the RecordTranscribe instance on the client.
    """
    # Check if SONIOX_API_KEY environment variable is set
    soniox_api_key = os.getenv("SONIOX_API_KEY")  # ← YOUR main API key
    
    # Get SONIOX_API_HOST or use default
    soniox_api_host = os.getenv("SONIOX_API_HOST", "https://api.soniox.com")

    try:
        async with httpx.AsyncClient() as client:
            # Call Soniox API to generate temporary key
            response = await client.post(
                f"{soniox_api_host}/v1/auth/temporary-api-key",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {soniox_api_key}",  # ← Uses YOUR main key
                },
                json={
                    "usage_type": "transcribe_websocket",
                    "expires_in_seconds": 60,  # ← Expires in 60 seconds
                },
            )

            # Parse the response
            data = response.json()

            return TemporaryKeyResponse(apiKey=data["api_key"])  # ← Returns temporary key
```

**What this does**: 
1. Your server has YOUR main API key (from environment variable)
2. Server calls Soniox API using YOUR main key
3. Soniox returns a temporary key (expires in 60 seconds)
4. Server returns temporary key to client

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ CLIENT (Browser)                                              │
│                                                               │
│ 1. transcribe.tsx calls:                                     │
│    useSonioxClient({ apiKey: getAPIKey })                    │
│                                                               │
│ 2. SDK calls getAPIKey() function:                          │
│    fetch('http://localhost:8000/v1/auth/temporary-api-key')  │
│                                                               │
│ 3. Receives temporary key:                                   │
│    "temp:WYJ67RBEFUWQXXPKYPD2UGXKWB"                         │
│                                                               │
│ 4. Uses temporary key to connect to Soniox                  │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP Request
┌─────────────────────────────────────────────────────────────┐
│ YOUR SERVER (localhost:8000)                                │
│                                                               │
│ 1. Receives request for temporary key                        │
│                                                               │
│ 2. Has YOUR main API key (from env):                         │
│    SONIOX_API_KEY="sk_1234567890abcdef..."                   │
│                                                               │
│ 3. Calls Soniox API:                                         │
│    POST https://api.soniox.com/v1/auth/temporary-api-key     │
│    Authorization: Bearer sk_1234567890abcdef...            │
│    Body: { "usage_type": "transcribe_websocket",             │
│            "expires_in_seconds": 60 }                        │
│                                                               │
│ 4. Receives temporary key from Soniox                        │
│                                                               │
│ 5. Returns temporary key to client                           │
└─────────────────────────────────────────────────────────────┘
                          ↓ API Call
┌─────────────────────────────────────────────────────────────┐
│ SONIOX API                                                   │
│                                                               │
│ 1. Validates YOUR main API key                              │
│                                                               │
│ 2. Generates temporary key                                   │
│                                                               │
│ 3. Returns:                                                  │
│    { "api_key": "temp:WYJ67RBEFUWQXXPKYPD2UGXKWB",          │
│      "expires_at": "2025-02-22T22:47:37.150Z" }             │
└─────────────────────────────────────────────────────────────┘
```

---

## Evidence from Code

### Evidence 1: Comment in Code
```typescript
// Fetch temporary API key from the server, so we can establish websocket connection.
// Read more on: https://soniox.com/docs/speech-to-text/guides/direct-stream#temporary-api-keys
```

**This explicitly says**: "Fetch temporary API key"

### Evidence 2: Server Endpoint Name
```python
@app.post("/v1/auth/temporary-api-key")  # ← Endpoint name says "temporary"
```

### Evidence 3: Server Comment
```python
"""
Generate a temporary API key for Soniox WebSocket transcription.

You don't want to expose the API key to the client, so we generate a temporary one.
Temporary API keys are then used to initialize the RecordTranscribe instance on the client.
"""
```

**This explicitly explains**: Why temporary keys are used (security)

### Evidence 4: Expiry Time
```python
json={
    "usage_type": "transcribe_websocket",
    "expires_in_seconds": 60,  # ← Temporary key expires in 60 seconds
}
```

**This shows**: Temporary keys have expiration

---

## What This Means

✅ **The official Soniox example DOES use temporary API keys**

✅ **This is the recommended approach** (as stated in Soniox documentation)

✅ **Your main API key stays on the server** (never exposed to client)

✅ **Temporary keys are generated on-demand** (when client needs them)

✅ **Temporary keys expire quickly** (60 seconds)

---

## Comparison: What You Saw When Running the Example

When you ran the example:

1. **Server started** on `localhost:8000` with YOUR main API key
2. **Client started** on `localhost:5173`
3. **Client requested temporary key** from server
4. **Server generated temporary key** using YOUR main key
5. **Client used temporary key** to connect to Soniox
6. **Transcription worked** ✅

**You never saw your main API key in the browser** - only temporary keys!

---

## Conclusion

**Yes, the official Soniox example you just ran uses temporary API keys.**

This is:
- ✅ The recommended approach
- ✅ The secure approach
- ✅ What we should implement in your app
- ✅ Industry best practice

The example demonstrates exactly how to do it correctly!

