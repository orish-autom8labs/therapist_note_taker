#!/bin/bash
# Promote staging revisions to production (100% traffic)
set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_ID="therapistnottaker"
REGION="us-central1"

echo -e "${BLUE}=== Promote Staging to Production ===${NC}"
echo ""

# Set project
gcloud config set project ${PROJECT_ID}

# Promote backend
echo -e "${YELLOW}Promoting backend...${NC}"
gcloud run services update-traffic note-taker-backend \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --to-latest

echo -e "${GREEN}Backend promoted to production${NC}"

# Promote frontend
echo -e "${YELLOW}Promoting frontend...${NC}"
gcloud run services update-traffic note-taker-frontend \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --to-latest

echo -e "${GREEN}Frontend promoted to production${NC}"

echo ""
echo -e "${GREEN}=== Promotion Complete! ===${NC}"
echo -e "Backend:  https://note-taker-backend-1049928242674.us-central1.run.app"
echo -e "Frontend: https://note-taker-frontend-1049928242674.us-central1.run.app"
