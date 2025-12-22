# Fix Node.js Version for Soniox Example

## Problem

The Soniox example requires Node.js 20.19.0+ or 22.12.0+, but you have 18.20.8.

## Solution: Upgrade Node.js using nvm

Since you have `nvm` installed, you can easily upgrade:

### Option 1: Install Latest LTS (Recommended)

```bash
nvm install --lts
nvm use --lts
nvm alias default lts/*
```

### Option 2: Install Specific Version

```bash
# Install Node 20 (LTS)
nvm install 20
nvm use 20
nvm alias default 20

# OR Install Node 22 (Latest)
nvm install 22
nvm use 22
nvm alias default 22
```

### Verify Installation

```bash
node --version
# Should show v20.x.x or v22.x.x
```

### Then Run the Example

```bash
cd /Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/react
npm install  # Reinstall with correct Node version
npm run dev
```

## Note

The warning is just a warning - Vite might still work with Node 18, but it's better to use the recommended version to avoid potential issues.

