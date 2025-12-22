#!/bin/bash

echo "=== Temporary API Key Verification Script ==="
echo ""
echo "Step 1: Generating temporary API key from our server..."
RESPONSE=$(curl -s -X POST http://localhost:3001/v1/auth/temporary-api-key)
echo "Response: $RESPONSE"
echo ""

# Extract the API key using jq
TEMP_KEY=$(echo $RESPONSE | jq -r '.apiKey')
echo "Extracted key: $TEMP_KEY"
echo ""

if [ "$TEMP_KEY" == "null" ] || [ -z "$TEMP_KEY" ]; then
    echo "❌ ERROR: Failed to get temporary API key from server"
    echo "Make sure server is running on port 3001"
    exit 1
fi

echo "Step 2: Testing if this temporary key is valid by attempting to use it..."
echo "(Opening a manual SDK test - check browser console)"
echo ""

# Create a test HTML file that uses this specific key
cat > /tmp/test_specific_key.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Test Specific Temporary Key</title>
    <script type="module">
        import { SonioxClient } from 'https://cdn.jsdelivr.net/npm/@soniox/speech-to-text-web@1.2.0/dist/index.mjs';

        const TEMP_KEY = "$TEMP_KEY";

        console.log('[TEST] Using temporary key:', TEMP_KEY);

        const client = new SonioxClient({
            apiKey: async () => {
                console.log('[TEST] SDK requesting API key...');
                console.log('[TEST] Returning:', TEMP_KEY);
                return TEMP_KEY;
            }
        });

        console.log('[TEST] Starting SDK...');

        client.start({
            model: 'stt-rt-v3',
            enableLanguageIdentification: true,
            enableSpeakerDiarization: true,

            onStarted: () => {
                console.log('[TEST] ✅✅✅ SUCCESS! Temporary key is VALID!');
                alert('✅ SUCCESS! The temporary key works!');
            },

            onError: (status, message, errorCode) => {
                console.error('[TEST] ❌❌❌ FAILURE!', { status, message, errorCode });
                alert('❌ FAILURE: ' + message);
            },

            onPartialResult: (result) => {
                console.log('[TEST] 📝 Received tokens:', result.tokens.length);
            },

            onStateChange: ({ newState }) => {
                console.log('[TEST] State:', newState);
            }
        });

        console.log('[TEST] SDK start() called - waiting for callbacks...');
    </script>
</head>
<body>
    <h1>Testing Temporary Key: <code>$TEMP_KEY</code></h1>
    <p>Open console (F12) to see results</p>
    <p>Allow microphone access when prompted</p>
    <hr>
    <p><strong>Expected:</strong></p>
    <ul>
        <li>✅ If key is valid: "SUCCESS! Temporary key is VALID!" alert</li>
        <li>❌ If key is invalid: "FAILURE: invalid temporary api key" alert</li>
    </ul>
</body>
</html>
EOF

echo "Opening test page in browser..."
open /tmp/test_specific_key.html

echo ""
echo "=== Instructions ==="
echo "1. Browser should open with test page"
echo "2. Open browser console (F12)"
echo "3. Allow microphone access when prompted"
echo "4. Watch for SUCCESS or FAILURE alert"
echo ""
echo "If SUCCESS: Temporary keys are valid, problem is elsewhere"
echo "If FAILURE: Temporary keys are being rejected by Soniox"
