#!/bin/bash
# Deploy Note Taker frontend to Google Cloud Run STAGING (no traffic)
set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID="therapistnottaker"
REGION="us-central1"
SERVICE_NAME="note-taker-frontend"
# Point to staging backend URL
BACKEND_URL="https://staging---note-taker-backend-1049928242674.us-central1.run.app"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}"

echo -e "${BLUE}=== Note Taker Frontend STAGING Deployment ===${NC}"
echo -e "${YELLOW}This deploys to staging (no traffic). Production is unaffected.${NC}"
echo ""

# Set project
gcloud config set project ${PROJECT_ID}

# Navigate to client directory
cd "$(dirname "$0")/../client"

# Build Docker image with staging backend URL
echo -e "${GREEN}Building Docker image...${NC}"
BUILD_TIME=$(date -u +"%Y%m%d-%H%M%S")
docker build \
    --platform linux/amd64 \
    --build-arg REACT_APP_API_URL=${BACKEND_URL} \
    --tag ${IMAGE_NAME}:staging-${BUILD_TIME} \
    --tag ${IMAGE_NAME}:staging-latest \
    .

echo -e "${GREEN}Image built${NC}"

# Configure Docker auth
echo -e "${GREEN}Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Push image
echo -e "${GREEN}Pushing image...${NC}"
docker push ${IMAGE_NAME}:staging-latest
docker push ${IMAGE_NAME}:staging-${BUILD_TIME}
echo -e "${GREEN}Image pushed${NC}"

# Deploy to Cloud Run with --no-traffic and --tag staging
echo -e "${GREEN}Deploying to Cloud Run (staging, no traffic)...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME}:staging-latest \
    --platform=managed \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --memory=512Mi \
    --cpu=1 \
    --timeout=60 \
    --port=8080 \
    --allow-unauthenticated \
    --no-traffic \
    --tag=staging

echo ""
echo -e "${GREEN}=== Staging Deployment Complete! ===${NC}"
echo -e "${YELLOW}Production is NOT affected. 0% traffic to this revision.${NC}"
echo ""

# Get staging URL
STAGING_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format='value(status.traffic[?tag=="staging"].url)')

echo -e "${YELLOW}Staging URL:${NC} ${STAGING_URL}"
echo ""
echo -e "To promote to production: ${BLUE}./scripts/promote_staging.sh${NC}"
