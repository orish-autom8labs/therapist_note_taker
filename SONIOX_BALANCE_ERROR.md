# Soniox Balance Error - Solution

## Problem Identified

The Soniox API is returning an error:
```json
{
  "error_code": 402,
  "error_message": "Organization balance exhausted. Please either add funds manually or enable autopay."
}
```

This means your Soniox account has run out of credits/balance.

## What I Fixed

I've updated the error detection in `soniox_provider.py` to properly detect Soniox error responses. The code now checks for:
- `error_code` and `error_message` (Soniox's format)
- `error` (generic format)
- `status` (alternative format)

When an error is detected, the session will now:
1. Properly detect the error
2. Stop the streaming session
3. Show a clear error message to the user

## Solution

You need to add funds to your Soniox account:

1. **Go to Soniox Console**: https://soniox.com/console
2. **Navigate to Billing/Payments**
3. **Add funds** or **enable autopay**

## After Adding Funds

1. **Restart your server** (to pick up the code changes):
   ```bash
   cd server
   # Stop server (Ctrl+C)
   source venv/bin/activate
   python run.py
   ```

2. **Try starting a session again** - it should work once you have balance

## Alternative: Use Mock Provider for Testing

While you're waiting to add funds, you can test the rest of the system with the mock provider:

```bash
# In server/.env, change:
TRANSCRIPTION_PROVIDER=mock
```

Then restart the server. This will let you test:
- WebSocket connections
- Audio streaming
- Session management
- Google Drive integration
- Email notifications

All without using Soniox credits.

## Error Message

After the fix, when Soniox returns a balance error, users will see:
```
Soniox error 402: Organization balance exhausted. Please either add funds manually or enable autopay.
```

This will appear in the browser UI and server logs.




