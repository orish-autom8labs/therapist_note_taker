# Deployment Guide

This guide explains how to deploy the Note Taker application to Google Cloud Run.

---

## Production URLs

| Service | URL |
|---------|-----|
| Frontend | https://note-taker-frontend-1049928242674.us-central1.run.app |
| Backend | https://note-taker-backend-1049928242674.us-central1.run.app |
| Health Check | https://note-taker-backend-1049928242674.us-central1.run.app/health |

---

## Prerequisites

### 1. Install Required Tools

```bash
# Google Cloud CLI
brew install google-cloud-sdk

# Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop
```

### 2. Authenticate with Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set up application default credentials
gcloud auth application-default login

# Set the project
gcloud config set project therapistnottaker
```

### 3. Verify Docker is Running

Make sure Docker Desktop is running before deploying.

---

## Quick Deployment Commands

### Deploy Backend Only
```bash
./scripts/deploy_backend.sh
```

### Deploy Frontend Only
```bash
./scripts/deploy_frontend.sh
```

### Deploy Both (Backend First)
```bash
./scripts/deploy_backend.sh && ./scripts/deploy_frontend.sh
```

**Important:** Always deploy backend first if you've made backend changes, because the frontend build embeds the backend URL.

---

## What the Scripts Do

### Backend Deployment (`scripts/deploy_backend.sh`)

1. Builds Docker image from `server/Dockerfile`
2. Pushes to Google Artifact Registry
3. Deploys to Cloud Run with:
   - 1GB memory, 1 CPU
   - 300s timeout (for long summarization requests)
   - Environment variables from `server/.env.yaml`

### Frontend Deployment (`scripts/deploy_frontend.sh`)

1. Builds Docker image from `client/Dockerfile`
2. Injects `REACT_APP_API_URL` pointing to backend
3. Pushes to Google Artifact Registry
4. Deploys to Cloud Run with:
   - 512MB memory, 1 CPU
   - 60s timeout

---

## Environment Configuration

### Backend Environment (`server/.env.yaml`)

This file contains production secrets and is used during Cloud Run deployment:

```yaml
TRANSCRIPTION_PROVIDER: "soniox"
NODE_ENV: "production"
FRONTEND_URL: "https://note-taker-frontend-1049928242674.us-central1.run.app"
SONIOX_API_KEY: "your-soniox-key"
GOOGLE_CLIENT_ID: "your-google-client-id"
GOOGLE_CLIENT_SECRET: "your-google-client-secret"
GOOGLE_REDIRECT_URI: "https://note-taker-backend-1049928242674.us-central1.run.app/auth/google/callback"
```

**Note:** The `.env.yaml` file is gitignored. Keep it secure and never commit it.

### Local Development (`server/.env`)

For local development, use the `.env` file with localhost URLs:

```bash
GOOGLE_REDIRECT_URI=http://localhost:3001/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

---

## Troubleshooting

### Authentication Errors

If you see `UNAUTHENTICATED` or `unauthorized: authentication failed`:

```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Reconfigure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Docker Build Fails

```bash
# Make sure Docker Desktop is running
# Check Docker status
docker info

# If on Mac with Apple Silicon, the scripts already use --platform linux/amd64
```

### Cloud Run Deployment Fails

```bash
# Check logs
gcloud run services logs read note-taker-backend --region=us-central1

# Check service status
gcloud run services describe note-taker-backend --region=us-central1
```

### CORS Errors in Browser

The backend CORS is configured in `server/main.py`. Ensure the frontend URL is in the allowed origins:

```python
allow_origins=[
    "http://localhost:3000",
    "https://note-taker-frontend-1049928242674.us-central1.run.app"
]
```

---

## Deployment Checklist

### Before Deploying

- [ ] Docker Desktop is running
- [ ] Authenticated with `gcloud auth login`
- [ ] `server/.env.yaml` has correct production values
- [ ] Code changes are tested locally

### After Deploying

- [ ] Visit frontend URL and verify it loads
- [ ] Check backend health: `curl https://note-taker-backend-1049928242674.us-central1.run.app/health`
- [ ] Test Google OAuth login flow
- [ ] Test a short recording session
- [ ] Verify transcript saves to Google Drive

---

## Google Cloud Console

- **Project:** therapistnottaker
- **Region:** us-central1
- **Console URL:** https://console.cloud.google.com/run?project=therapistnottaker

---

## OAuth Configuration

### How OAuth Works

OAuth allows customers to log in with their Google account. You never see their password.

```
1. Customer clicks "Sign in with Google"
2. Google shows login page (Google's website)
3. Customer enters their Google credentials
4. Customer authorizes your app to access their Google Drive
5. Google gives your app a temporary access token
6. Your app uses this token to save files to customer's Drive
```

### Google Cloud Console OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials?project=therapistnottaker)
2. Under "OAuth 2.0 Client IDs", click on the web client
3. Ensure these redirect URIs are configured:
   - `http://localhost:3001/auth/google/callback` (development)
   - `https://note-taker-backend-1049928242674.us-central1.run.app/auth/google/callback` (production)

### What Data is Stored

- **Access tokens** - temporary, expire in ~1 hour
- **Refresh tokens** - to get new access tokens
- **NO passwords** - Google handles authentication
- **Transcripts** - temporarily, then saved to customer's Google Drive

---

## Cost Considerations

| Service | Cost |
|---------|------|
| Google Cloud Run | Pay per request (~$0-5/month for low usage) |
| Google OAuth | Free |
| Soniox Transcription | Pay per minute transcribed |
| Google Drive Storage | Free 15GB per user |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (React)                                            │
│  └── Cloud Run: note-taker-frontend                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│  FastAPI Backend                                            │
│  └── Cloud Run: note-taker-backend                         │
│      ├── /v1/auth/temporary-api-key → Soniox               │
│      ├── /auth/google/* → Google OAuth                     │
│      └── /api/sessions/*/transcript → Google Drive         │
└─────────────────────────────────────────────────────────────┘
```




