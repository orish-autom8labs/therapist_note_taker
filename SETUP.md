# Setup Guide

## Prerequisites

1. **Node.js 18+** - [Download](https://nodejs.org/)
2. **Google Cloud Account** - For Drive integration
3. **Transcription Provider API Key**:
   - **Soniox** (recommended): Sign up at [soniox.com](https://soniox.com)
   - **Google Cloud Speech-to-Text**: Enable API in Google Cloud Console

## Step 1: Install Dependencies

### Backend (Python)
```bash
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend (JavaScript/React)
```bash
cd client
npm install
```

Or install all at once:
```bash
# Backend
cd server && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ..

# Frontend
cd client && npm install && cd ..
```

## Step 2: Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure:
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:3001/auth/google/callback`
6. Copy **Client ID** and **Client Secret**

## Step 3: Configure Transcription Provider

### Option A: Soniox (Recommended)

1. Sign up at [soniox.com](https://soniox.com)
2. Get your API key from dashboard
3. Set in environment variables (see Step 4)

### Option B: Google Cloud Speech-to-Text

1. Enable **Cloud Speech-to-Text API** in Google Cloud Console
2. Create a service account
3. Download JSON credentials
4. Set in environment variables (see Step 4)

## Step 4: Configure Environment Variables

Create `server/.env` file (or set environment variables):

```bash
# Server Configuration
PORT=3001
NODE_ENV=development

# Transcription Provider
# Options: 'soniox', 'google'
TRANSCRIPTION_PROVIDER=soniox

# Soniox Configuration
SONIOX_API_KEY=your_soniox_api_key_here

# Google Cloud Speech-to-Text (if using Google)
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CREDENTIALS={"type":"service_account",...}

# Google OAuth (for Drive access)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3001/auth/google/callback

# Email Configuration
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_sendgrid_api_key
# OR use SMTP:
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your_email@gmail.com
# SMTP_PASSWORD=your_app_password

EMAIL_FROM=noreply@notetaker.com
ADMIN_EMAIL=admin@example.com
```

## Step 5: Run the Application

### Development Mode

You need to run backend and frontend separately:

**Terminal 1 - Backend (Python):**
```bash
cd server
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run.py
# Or: python -m uvicorn main:app --reload
```

**Terminal 2 - Frontend (React):**
```bash
cd client
npm start
```

This will start:
- Backend server on `http://localhost:3001`
- Frontend on `http://localhost:3000`

## Step 6: Test the Application

1. Open `http://localhost:3000` in your browser
2. Click "Sign in with Google"
3. Authorize the app to access Google Drive
4. Enter a patient name
5. Click "Start Session"
6. Allow microphone access
7. Start speaking (Hebrew recommended)
8. Click "Stop & Save" when done

## Switching Transcription Providers

To switch providers, simply change the `TRANSCRIPTION_PROVIDER` in `server/.env`:

```bash
# Use Soniox
TRANSCRIPTION_PROVIDER=soniox

# Use Google
TRANSCRIPTION_PROVIDER=google
```

Then restart the server.

## Troubleshooting

### Microphone not working
- Check browser permissions
- Use HTTPS in production (required for microphone access)
- Try a different browser

### Google OAuth errors
- Verify redirect URI matches exactly
- Check that Google Drive API is enabled
- Ensure credentials are correct

### Transcription not working
- Verify API key is correct
- Check network connection
- Review server logs for errors

### Auto-save not working
- Check Google Drive permissions
- Verify folder path exists
- Check server logs

## Production Deployment

1. Set `NODE_ENV=production`
2. Update `GOOGLE_REDIRECT_URI` to production URL
3. Build frontend: `npm run build`
4. Serve frontend build folder
5. Set up HTTPS (required for microphone access)
6. Configure email service
7. Set up cron job for temp file cleanup (optional)

## Notes

- **Soniox Provider**: The Soniox SDK may need to be installed separately or use their REST API. Check [Soniox documentation](https://docs.soniox.com) for the latest integration method.
- **Google Provider**: Requires `@google-cloud/speech` package and service account credentials.
- **Auto-save**: Saves to Drive every 1 minute during active sessions.
- **Recovery**: Uses localStorage backup (every 5 seconds) + Drive temp files (every 1 minute).

