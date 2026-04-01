#!/bin/bash
# =============================================================================
# RAG Conversation System - Startup Script
# =============================================================================
# This script validates the environment, builds and starts all services,
# waits for them to become healthy, and provides access information.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Docker is installed and running
check_docker() {
    print_header "Checking Docker Environment"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker command found"
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose found"
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Create .env file from .env.example if it doesn't exist
setup_env_file() {
    print_header "Setting Up Environment"
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success ".env created from .env.example"
            print_warning "Please update .env with your API keys and configuration"
        else
            print_error ".env.example not found. Cannot create .env"
            exit 1
        fi
    else
        print_success ".env already exists"
    fi
}

# Build and start services
start_services() {
    print_header "Building and Starting Services"
    
    # Check if docker compose plugin is available
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Build all services
    print_info "Building Docker images..."
    $COMPOSE_CMD build --parallel
    print_success "All images built"
    
    # Start services
    print_info "Starting Docker containers..."
    $COMPOSE_CMD up -d
    print_success "All containers started"
}

# Wait for services to become healthy
wait_for_healthy() {
    print_header "Waiting for Services to Become Healthy"
    
    local services=("postgres" "redis" "auth-service" "query-service" "document-service" "conversation-service" "backend" "frontend")
    local max_attempts=60
    local attempt=0
    
    for service in "${services[@]}"; do
        print_info "Waiting for $service..."
        attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if docker inspect --format='{{.State.Health.Status}}' rag-$service 2>/dev/null | grep -q "healthy" 2>/dev/null; then
                print_success "$service is healthy"
                break
            fi
            
            # Check if container is running (for services without healthcheck)
            if docker inspect --format='{{.State.Running}}' rag-$service 2>/dev/null | grep -q "true" 2>/dev/null; then
                if [ "$service" == "backend" ] || [ "$service" == "frontend" ]; then
                    # These services might not have healthcheck defined the same way
                    sleep 2
                    print_success "$service is running"
                    break
                fi
            fi
            
            sleep 2
            attempt=$((attempt + 1))
        done
        
        if [ $attempt -ge $max_attempts ]; then
            print_warning "$service did not become healthy within timeout"
        fi
    done
}

# Show service status
show_status() {
    print_header "Service Status"
    
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    $COMPOSE_CMD ps
}

# Print access information
print_access_info() {
    print_header "Access Information"
    
    echo -e "${GREEN}Application is ready!${NC}\n"
    echo -e "  ${BLUE}Frontend:${NC}   http://localhost:3000"
    echo -e "  ${BLUE}API Gateway:${NC} http://localhost:8000"
    echo -e "  ${BLUE}Health Check:${NC} http://localhost:8000/health"
    echo -e ""
    echo -e "${YELLOW}Service Ports:${NC}"
    echo -e "  Auth Service:        8001"
    echo -e "  Query Service:       8002"
    echo -e "  Document Service:   8003"
    echo -e "  Conversation Service: 8004"
    echo -e "  PostgreSQL:          5432"
    echo -e "  Redis:               6379"
    echo -e ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo -e "  View logs:     ${BLUE}docker compose logs -f${NC}"
    echo -e "  Stop services: ${BLUE}docker compose down${NC}"
    echo -e "  Restart:       ${BLUE}docker compose restart${NC}"
}

# Main execution
main() {
    print_header "RAG Conversation System - Starting"
    
    check_docker
    setup_env_file
    start_services
    wait_for_healthy
    show_status
    print_access_info
    
    print_success "All services started successfully!"
}

# Run main function
main "$@"
