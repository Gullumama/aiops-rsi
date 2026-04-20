#!/bin/bash

set -e

echo "════════════════════════════════════════════════════════════"
echo "K8sGPT Custom Build Script"
echo "════════════════════════════════════════════════════════════"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REGISTRY=${1:-"k8sgpt"}
TAG=${2:-"latest"}
FULL_IMAGE_NAME="${REGISTRY}:${TAG}"

echo -e "\n${YELLOW}Building K8sGPT Docker image: ${FULL_IMAGE_NAME}${NC}\n"

# Build the image
docker build \
    -t "${FULL_IMAGE_NAME}" \
    -f k8sgpt/Dockerfile \
    --progress=plain \
    .

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Build successful!${NC}"
    echo -e "${GREEN}Image: ${FULL_IMAGE_NAME}${NC}"
    docker images | grep -E "REPOSITORY|${REGISTRY}"
else
    echo -e "\n${RED}✗ Build failed!${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Test the image:"
echo "   docker run ${FULL_IMAGE_NAME} version"
echo ""
echo "2. Push to registry:"
echo "   docker push ${FULL_IMAGE_NAME}"
echo ""
echo "3. Update deployment:"
echo "   kubectl set image deployment/k8sgpt k8sgpt=${FULL_IMAGE_NAME} -n aiops"