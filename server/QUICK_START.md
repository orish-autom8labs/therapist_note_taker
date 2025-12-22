# Quick Start - Adding Your Soniox API Key

## Step 1: Create `.env` file

In the `server/` directory, create a file named `.env`:

```bash
cd server
touch .env
# Or on Windows: type nul > .env
```

## Step 2: Add Your Soniox API Key

Open `server/.env` and add:

```bash
# Transcription Provider
TRANSCRIPTION_PROVIDER=soniox

# Soniox API Key
SONIOX_API_KEY=your_actual_api_key_here
```

**Replace `your_actual_api_key_here` with your actual Soniox API key.**

## Step 3: Verify It Works

Run the server and check the health endpoint:

```bash
# Make sure you're in the server directory
cd server

# Activate virtual environment (if you created one)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the server
python run.py
```

Then in another terminal:
```bash
curl http://localhost:3001/health
```

You should see:
```json
{
  "status": "ok",
  "provider": "Soniox"
}
```

## That's It!

Your Soniox API key is now configured. The server will automatically use it when you start a transcription session.

## Full `.env` Example

If you want to set up everything at once, here's a complete `.env` template:

```bash
# Server Configuration
PORT=3001
NODE_ENV=development

# Transcription Provider
TRANSCRIPTION_PROVIDER=soniox

# Soniox Configuration
SONIOX_API_KEY=your_soniox_api_key_here

# Google OAuth (for Drive access - needed for saving transcripts)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3001/auth/google/callback

# Email Configuration (optional for MVP)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_FROM=noreply@notetaker.com
```

**For MVP, you only need:**
- `SONIOX_API_KEY` (required)
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (for Drive integration)




