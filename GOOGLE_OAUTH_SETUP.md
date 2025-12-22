# Quick Google OAuth Setup

## The Error
You're seeing "Missing required parameter: client_id" because Google OAuth isn't configured yet.

## Quick Setup (5 minutes)

### Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Sign in with your Google account
3. Create a new project (or select existing):
   - Click project dropdown at top
   - Click "New Project"
   - Name it "Note Taker" (or any name)
   - Click "Create"

### Step 2: Enable Google Drive API
1. In the project, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and click "Enable"

### Step 3: Create OAuth Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: "External" (for personal use)
   - App name: "Note Taker"
   - User support email: your email
   - Developer contact: your email
   - Click "Save and Continue" through the steps
4. Back to creating OAuth client ID:
   - Application type: **Web application**
   - Name: "Note Taker Web Client"
   - Authorized redirect URIs: 
     ```
     http://localhost:3001/auth/google/callback
     ```
   - Click "Create"
5. **Copy the Client ID and Client Secret** (you'll see them in a popup)

### Step 4: Add to .env file
Add these lines to `server/.env`:

```bash
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3001/auth/google/callback
```

Replace `your_client_id_here` and `your_client_secret_here` with the actual values from Step 3.

### Step 5: Restart the server
After adding the credentials, restart your Python server:
```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd server
source venv/bin/activate
python run.py
```

## That's It!
After restarting, try "Sign in with Google" again. It should work!

## Troubleshooting

**"Redirect URI mismatch" error:**
- Make sure the redirect URI in Google Console exactly matches:
  `http://localhost:3001/auth/google/callback`
- No trailing slashes, exact match

**Still not working?**
- Check that `.env` file has no extra spaces
- Make sure you restarted the server after adding credentials
- Check server logs for error messages




