# Debugging Guide

## The Problem

The Soniox provider is **not implemented yet** - it's just a template. The `send_audio` function does nothing, so transcription won't work.

## How to Debug

### Step 1: Check Browser Console
1. Open browser DevTools (F12 or Cmd+Option+I)
2. Go to "Console" tab
3. Look for errors (red text)
4. Common errors:
   - WebSocket connection failed
   - CORS errors
   - Audio permission errors

### Step 2: Check Server Logs
Look at your terminal where `python run.py` is running:
- Look for error messages
- Look for WebSocket connection messages
- Look for transcription errors

### Step 3: Check Network Tab
1. In DevTools, go to "Network" tab
2. Filter by "WS" (WebSocket)
3. Check if WebSocket connection is established
4. Look for failed requests

### Step 4: Test WebSocket Connection
Open browser console and run:
```javascript
const ws = new WebSocket('ws://localhost:3001/ws');
ws.onopen = () => console.log('✅ WebSocket connected');
ws.onerror = (e) => console.error('❌ WebSocket error:', e);
ws.onmessage = (e) => console.log('📨 Message:', e.data);
```

## Current Issue: Soniox Not Implemented

The Soniox provider needs actual API integration. You have two options:

### Option 1: Use Mock Provider (For Testing)
I'll create a mock provider that simulates transcription so you can test the UI flow.

### Option 2: Implement Soniox API
You need to:
1. Check Soniox documentation
2. Install Soniox SDK or use REST API
3. Implement the actual API calls

## Quick Fix: Use Mock Provider

I'll create a mock provider that generates fake transcripts so you can test the full flow.




