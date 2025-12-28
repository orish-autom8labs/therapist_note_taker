#!/bin/bash
# Deploy Note Taker backend to Google Cloud Run
set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID="therapistnottaker"
REGION="us-central1"
SERVICE_NAME="note-taker-backend"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}"

echo -e "${BLUE}=== Note Taker Backend Deployment ===${NC}"
echo ""

# Set project
gcloud config set project ${PROJECT_ID}

# Navigate to server directory
cd "$(dirname "$0")/../server"

# Build Docker image
echo -e "${GREEN}Building Docker image...${NC}"
BUILD_TIME=$(date -u +"%Y%m%d-%H%M%S")
docker build \
    --platform linux/amd64 \
    --tag ${IMAGE_NAME}:latest \
    --tag ${IMAGE_NAME}:${BUILD_TIME} \
    .

echo -e "${GREEN}✓ Image built${NC}"

# Configure Docker auth
echo -e "${GREEN}Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Push image
echo -e "${GREEN}Pushing image...${NC}"
docker push ${IMAGE_NAME}:latest
docker push ${IMAGE_NAME}:${BUILD_TIME}
echo -e "${GREEN}✓ Image pushed${NC}"

# Deploy to Cloud Run
echo -e "${GREEN}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME}:latest \
    --platform=managed \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --memory=1Gi \
    --cpu=1 \
    --timeout=300 \
    --port=8080 \
    --allow-unauthenticated \
    --env-vars-file=.env.yaml

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format='value(status.url)')

echo -e "${YELLOW}Service URL:${NC} ${SERVICE_URL}"
echo ""
