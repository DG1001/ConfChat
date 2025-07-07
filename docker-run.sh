#!/bin/bash

# PresentAI - Docker Run Script
# Einfacher Start des Docker Containers mit konfigurierbaren Optionen

set -e

# Default values
DEFAULT_PORT=8080
DEFAULT_IMAGE="ghcr.io/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/' | tr '[:upper:]' '[:lower:]')/confchat:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo -e "${BLUE}PresentAI Docker Runner${NC}"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -p, --port PORT        External port (default: $DEFAULT_PORT)"
    echo "  -i, --image IMAGE      Docker image (default: auto-detect)"
    echo "  -d, --detach          Run in background"
    echo "  -e, --env-file FILE   Load environment from file"
    echo "  --build               Build image locally instead of pulling"
    echo "  --stop                Stop running container"
    echo "  --logs                Show container logs"
    echo "  -h, --help            Show this help"
    echo
    echo "Environment Variables (required):"
    echo "  OPENAI_API_KEY        Your OpenAI API key"
    echo
    echo "Environment Variables (optional):"
    echo "  REGISTRATION_PASSWORD Custom registration password"
    echo "  SECRET_KEY           Custom Flask secret key"
    echo
    echo "Examples:"
    echo "  # Basic run with environment variables"
    echo "  OPENAI_API_KEY=sk-... $0"
    echo
    echo "  # Run on custom port"
    echo "  OPENAI_API_KEY=sk-... $0 --port 9000"
    echo
    echo "  # Run with environment file"
    echo "  $0 --env-file .env"
    echo
    echo "  # Build and run locally"
    echo "  OPENAI_API_KEY=sk-... $0 --build"
}

# Parse command line arguments
PORT=$DEFAULT_PORT
IMAGE=$DEFAULT_IMAGE
DETACH=""
ENV_FILE=""
BUILD=false
ACTION="run"

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE="$2"
            shift 2
            ;;
        -d|--detach)
            DETACH="-d"
            shift
            ;;
        -e|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --stop)
            ACTION="stop"
            shift
            ;;
        --logs)
            ACTION="logs"
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

CONTAINER_NAME="presentai"

# Handle different actions
case $ACTION in
    "stop")
        echo -e "${YELLOW}Stopping PresentAI container...${NC}"
        docker stop $CONTAINER_NAME 2>/dev/null || echo "Container not running"
        docker rm $CONTAINER_NAME 2>/dev/null || echo "Container not found"
        echo -e "${GREEN}Container stopped${NC}"
        exit 0
        ;;
    "logs")
        echo -e "${BLUE}Showing PresentAI container logs...${NC}"
        docker logs -f $CONTAINER_NAME
        exit 0
        ;;
esac

# Validate environment
if [[ -z "$ENV_FILE" && -z "$OPENAI_API_KEY" ]]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable is required${NC}"
    echo "Either set it directly or use --env-file option"
    exit 1
fi

# Stop existing container if running
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Build image if requested
if [[ "$BUILD" == "true" ]]; then
    echo -e "${BLUE}Building Docker image locally...${NC}"
    docker build -t $CONTAINER_NAME .
    IMAGE=$CONTAINER_NAME
else
    echo -e "${BLUE}Using Docker image: $IMAGE${NC}"
    # Try to pull latest image
    docker pull $IMAGE 2>/dev/null || echo -e "${YELLOW}Warning: Could not pull image, using local version${NC}"
fi

# Prepare docker run command
DOCKER_CMD="docker run --name $CONTAINER_NAME -p $PORT:5000"

# Add detach flag if specified
if [[ -n "$DETACH" ]]; then
    DOCKER_CMD="$DOCKER_CMD $DETACH"
fi

# Add environment variables
if [[ -n "$ENV_FILE" ]]; then
    if [[ -f "$ENV_FILE" ]]; then
        DOCKER_CMD="$DOCKER_CMD --env-file $ENV_FILE"
        echo -e "${GREEN}Loading environment from: $ENV_FILE${NC}"
    else
        echo -e "${RED}Error: Environment file not found: $ENV_FILE${NC}"
        exit 1
    fi
else
    DOCKER_CMD="$DOCKER_CMD -e OPENAI_API_KEY=$OPENAI_API_KEY"
    [[ -n "$REGISTRATION_PASSWORD" ]] && DOCKER_CMD="$DOCKER_CMD -e REGISTRATION_PASSWORD=$REGISTRATION_PASSWORD"
    [[ -n "$SECRET_KEY" ]] && DOCKER_CMD="$DOCKER_CMD -e SECRET_KEY=$SECRET_KEY"
fi

# Add volume for database persistence
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/instance:/app/instance"

# Add image name
DOCKER_CMD="$DOCKER_CMD $IMAGE"

echo -e "${BLUE}Starting PresentAI container...${NC}"
echo -e "${YELLOW}Port: $PORT${NC}"
echo -e "${YELLOW}Container: $CONTAINER_NAME${NC}"
echo

# Run the container
eval $DOCKER_CMD

if [[ -n "$DETACH" ]]; then
    echo -e "${GREEN}✅ PresentAI started successfully!${NC}"
    echo
    echo -e "${BLUE}Access the application at:${NC} http://localhost:$PORT"
    echo
    echo "Container management:"
    echo "  View logs:    $0 --logs"
    echo "  Stop:         $0 --stop"
    echo "  Restart:      $0 --stop && $0"
else
    echo -e "${GREEN}✅ PresentAI container finished${NC}"
fi