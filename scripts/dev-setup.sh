#!/bin/bash

# Sound Pesa Platform - Development Environment Setup Script
# This script sets up the complete development environment for the Sound Pesa platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command_exists node; then
        missing_deps+=("node")
    fi
    
    if ! command_exists npm; then
        missing_deps+=("npm")
    fi
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and run this script again."
        log_info "Installation guides:"
        log_info "  Docker: https://docs.docker.com/get-docker/"
        log_info "  Node.js: https://nodejs.org/en/download/"
        log_info "  Python: https://www.python.org/downloads/"
        exit 1
    fi
    
    # Check Docker version
    local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    local required_docker_version="20.10"
    
    if [ "$(printf '%s\n' "$required_docker_version" "$docker_version" | sort -V | head -n1)" != "$required_docker_version" ]; then
        log_warning "Docker version $docker_version detected. Recommended version is $required_docker_version or higher."
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    log_success "All prerequisites are satisfied"
}

# Setup environment files
setup_environment() {
    log_info "Setting up environment files..."
    
    # Root .env file
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_success "Created .env from .env.example"
        else
            log_warning ".env.example not found, creating basic .env file"
            cat > .env << EOF
# Sound Pesa Platform Environment Configuration
COMPOSE_PROJECT_NAME=sound-pesa
ENVIRONMENT=development

# Database Configuration
POSTGRES_DB=soundpesa
POSTGRES_USER=soundpesa
POSTGRES_PASSWORD=soundpesa_dev_password

# Redis Configuration
REDIS_PASSWORD=redis_dev_password

# Vault Configuration
VAULT_DEV_ROOT_TOKEN_ID=dev-root-token
VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200

# API Configuration
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DJANGO_DEBUG=True
JWT_SECRET_KEY=jwt-dev-secret-key

# Blockchain Configuration (Development/Testnet)
BITCOIN_NETWORK=testnet
ETHEREUM_NETWORK=goerli
CARDANO_NETWORK=testnet
POLKADOT_NETWORK=westend
EOF
        fi
    else
        log_info ".env file already exists, skipping creation"
    fi
    
    # API environment file
    if [ ! -f packages/api/.env ]; then
        if [ -f packages/api/.env.example ]; then
            cp packages/api/.env.example packages/api/.env
            log_success "Created packages/api/.env from .env.example"
        else
            log_warning "packages/api/.env.example not found, creating basic API .env file"
            mkdir -p packages/api
            cat > packages/api/.env << EOF
# Django Configuration
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,api

# Database Configuration
DATABASE_URL=postgresql://soundpesa:soundpesa_dev_password@postgres:5432/soundpesa

# Redis Configuration
REDIS_URL=redis://:redis_dev_password@redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://:redis_dev_password@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redis_dev_password@redis:6379/2

# Vault Configuration
VAULT_URL=http://vault:8200
VAULT_TOKEN=dev-root-token

# JWT Configuration
JWT_SECRET_KEY=jwt-dev-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=86400

# Blockchain Node Configuration
BITCOIN_RPC_URL=http://bitcoin-core:8332
BITCOIN_RPC_USER=bitcoin
BITCOIN_RPC_PASSWORD=bitcoin_rpc_password

ETHEREUM_RPC_URL=http://geth:8545
ETHEREUM_WS_URL=ws://geth:8546

CARDANO_NODE_SOCKET=/opt/cardano/db/socket
CARDANO_NETWORK=testnet

POLKADOT_WS_URL=ws://polkadot:9944
EOF
        fi
    else
        log_info "packages/api/.env file already exists, skipping creation"
    fi
    
    # Web environment file
    if [ ! -f packages/web/.env.local ]; then
        if [ -f packages/web/.env.example ]; then
            cp packages/web/.env.example packages/web/.env.local
            log_success "Created packages/web/.env.local from .env.example"
        else
            log_warning "packages/web/.env.example not found, creating basic web .env file"
            mkdir -p packages/web
            cat > packages/web/.env.local << EOF
# Next.js Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=nextauth-dev-secret

# PWA Configuration
NEXT_PUBLIC_PWA_NAME="Sound Pesa"
NEXT_PUBLIC_PWA_SHORT_NAME="SoundPesa"
NEXT_PUBLIC_PWA_DESCRIPTION="Multi-chain cryptocurrency wallet"

# Development Configuration
NODE_ENV=development
EOF
        fi
    else
        log_info "packages/web/.env.local file already exists, skipping creation"
    fi
    
    # Mobile app environment file
    if [ ! -f packages/app/.env ]; then
        if [ -f packages/app/.env.example ]; then
            cp packages/app/.env.example packages/app/.env
            log_success "Created packages/app/.env from .env.example"
        else
            log_warning "packages/app/.env.example not found, creating basic app .env file"
            mkdir -p packages/app
            cat > packages/app/.env << EOF
# Expo Configuration
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_WS_URL=ws://localhost:8000/ws

# App Configuration
EXPO_PUBLIC_APP_NAME="Sound Pesa"
EXPO_PUBLIC_APP_VERSION="1.0.0"

# Development Configuration
EXPO_PUBLIC_DEV_MODE=true
EOF
        fi
    else
        log_info "packages/app/.env file already exists, skipping creation"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Install shared package dependencies
    if [ -d packages/shared ]; then
        log_info "Installing shared package dependencies..."
        cd packages/shared
        npm install
        npm run build
        cd ../..
        log_success "Shared package dependencies installed"
    fi
    
    # Install web dependencies
    if [ -d packages/web ]; then
        log_info "Installing web application dependencies..."
        cd packages/web
        npm install
        cd ../..
        log_success "Web application dependencies installed"
    fi
    
    # Install mobile app dependencies
    if [ -d packages/app ]; then
        log_info "Installing mobile application dependencies..."
        cd packages/app
        npm install
        cd ../..
        log_success "Mobile application dependencies installed"
    fi
    
    # Install API dependencies (will be done in container)
    log_info "API dependencies will be installed in Docker container"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build all images
    docker-compose -f docker-compose.dev.yml build --no-cache
    
    log_success "Docker images built successfully"
}

# Initialize services
initialize_services() {
    log_info "Initializing services..."
    
    # Start core services first
    log_info "Starting core services (database, cache, vault)..."
    docker-compose -f docker-compose.dev.yml up -d postgres redis vault
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Initialize Vault (development mode)
    log_info "Initializing Vault..."
    docker-compose -f docker-compose.dev.yml exec -T vault vault auth -method=userpass username=admin password=admin || true
    
    # Start remaining services
    log_info "Starting remaining services..."
    docker-compose -f docker-compose.dev.yml up -d
    
    # Wait for API to be ready
    log_info "Waiting for API service to be ready..."
    sleep 15
    
    # Run database migrations
    log_info "Running database migrations..."
    docker-compose -f docker-compose.dev.yml exec -T api python manage.py migrate
    
    # Create superuser
    log_info "Creating Django superuser..."
    docker-compose -f docker-compose.dev.yml exec -T api python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@soundpesa.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
" || log_warning "Could not create superuser automatically"
    
    # Initialize Vault secrets
    log_info "Setting up Vault secrets..."
    docker-compose -f docker-compose.dev.yml exec -T vault sh -c "
vault kv put secret/api/database url='postgresql://soundpesa:soundpesa_dev_password@postgres:5432/soundpesa'
vault kv put secret/api/redis url='redis://:redis_dev_password@redis:6379/0'
vault kv put secret/api/jwt secret='jwt-dev-secret-key'
" || log_warning "Could not initialize Vault secrets"
    
    log_success "Services initialized successfully"
}

# Setup development tools
setup_dev_tools() {
    log_info "Setting up development tools..."
    
    # Create useful aliases
    cat > .dev_aliases << 'EOF'
# Sound Pesa Development Aliases
alias sp-up='docker-compose -f docker-compose.dev.yml up -d'
alias sp-down='docker-compose -f docker-compose.dev.yml down'
alias sp-logs='docker-compose -f docker-compose.dev.yml logs -f'
alias sp-api='docker-compose -f docker-compose.dev.yml exec api'
alias sp-web='docker-compose -f docker-compose.dev.yml exec web'
alias sp-db='docker-compose -f docker-compose.dev.yml exec postgres psql -U soundpesa -d soundpesa'
alias sp-redis='docker-compose -f docker-compose.dev.yml exec redis redis-cli'
alias sp-shell='docker-compose -f docker-compose.dev.yml exec api python manage.py shell'
alias sp-migrate='docker-compose -f docker-compose.dev.yml exec api python manage.py migrate'
alias sp-test='docker-compose -f docker-compose.dev.yml exec api python manage.py test'
alias sp-restart='docker-compose -f docker-compose.dev.yml restart'
alias sp-rebuild='docker-compose -f docker-compose.dev.yml build --no-cache'
EOF
    
    log_info "Development aliases created in .dev_aliases"
    log_info "Source them with: source .dev_aliases"
    
    # Create development scripts
    mkdir -p scripts/dev
    
    # Quick restart script
    cat > scripts/dev/restart.sh << 'EOF'
#!/bin/bash
echo "Restarting Sound Pesa development environment..."
docker-compose -f docker-compose.dev.yml restart
echo "Services restarted successfully"
EOF
    chmod +x scripts/dev/restart.sh
    
    # Logs script
    cat > scripts/dev/logs.sh << 'EOF'
#!/bin/bash
SERVICE=${1:-""}
if [ -z "$SERVICE" ]; then
    docker-compose -f docker-compose.dev.yml logs -f
else
    docker-compose -f docker-compose.dev.yml logs -f "$SERVICE"
fi
EOF
    chmod +x scripts/dev/logs.sh
    
    # Database reset script
    cat > scripts/dev/reset-db.sh << 'EOF'
#!/bin/bash
echo "Resetting database..."
docker-compose -f docker-compose.dev.yml stop api celery-worker
docker-compose -f docker-compose.dev.yml exec postgres psql -U soundpesa -c "DROP DATABASE IF EXISTS soundpesa;"
docker-compose -f docker-compose.dev.yml exec postgres psql -U soundpesa -c "CREATE DATABASE soundpesa;"
docker-compose -f docker-compose.dev.yml start api celery-worker
sleep 5
docker-compose -f docker-compose.dev.yml exec api python manage.py migrate
echo "Database reset complete"
EOF
    chmod +x scripts/dev/reset-db.sh
    
    log_success "Development tools set up successfully"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    local failed_checks=()
    
    # Check if services are running
    if ! docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
        failed_checks+=("Services not running")
    fi
    
    # Check API health
    if ! curl -s http://localhost:8000/api/health/ >/dev/null 2>&1; then
        failed_checks+=("API health check failed")
    fi
    
    # Check web application
    if ! curl -s http://localhost:3000 >/dev/null 2>&1; then
        failed_checks+=("Web application not accessible")
    fi
    
    # Check database connection
    if ! docker-compose -f docker-compose.dev.yml exec -T postgres psql -U soundpesa -d soundpesa -c "SELECT 1;" >/dev/null 2>&1; then
        failed_checks+=("Database connection failed")
    fi
    
    if [ ${#failed_checks[@]} -ne 0 ]; then
        log_warning "Some verification checks failed:"
        for check in "${failed_checks[@]}"; do
            log_warning "  - $check"
        done
        log_info "The setup may still be initializing. Wait a few minutes and check manually."
    else
        log_success "All verification checks passed!"
    fi
}

# Display access information
show_access_info() {
    log_success "Sound Pesa development environment setup complete!"
    echo
    log_info "Access URLs:"
    echo "  🌐 Web Application:     http://localhost:3000"
    echo "  🔧 API Documentation:  http://localhost:8000/api/docs/"
    echo "  👤 Admin Panel:        http://localhost:8000/admin/"
    echo "  📊 Grafana Dashboard:  http://localhost:3001 (admin/admin)"
    echo "  📈 Prometheus:         http://localhost:9090"
    echo "  🐰 RabbitMQ Management: http://localhost:15672 (guest/guest)"
    echo "  🌸 Celery Flower:      http://localhost:5555"
    echo
    log_info "Default Credentials:"
    echo "  Django Admin: admin / admin123"
    echo "  Grafana:      admin / admin"
    echo "  RabbitMQ:     guest / guest"
    echo
    log_info "Useful Commands:"
    echo "  View logs:           docker-compose -f docker-compose.dev.yml logs -f"
    echo "  Stop services:       docker-compose -f docker-compose.dev.yml down"
    echo "  Restart services:    docker-compose -f docker-compose.dev.yml restart"
    echo "  Django shell:        docker-compose -f docker-compose.dev.yml exec api python manage.py shell"
    echo "  Database shell:      docker-compose -f docker-compose.dev.yml exec postgres psql -U soundpesa -d soundpesa"
    echo
    log_info "Development aliases available in .dev_aliases (run: source .dev_aliases)"
    echo
    log_info "For troubleshooting, check: docs/troubleshooting.md"
}

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "Setup failed. Cleaning up..."
        docker-compose -f docker-compose.dev.yml down >/dev/null 2>&1 || true
    fi
}

# Main execution
main() {
    trap cleanup EXIT
    
    echo "=========================================="
    echo "  Sound Pesa Development Environment Setup"
    echo "=========================================="
    echo
    
    check_prerequisites
    setup_environment
    install_dependencies
    build_images
    initialize_services
    setup_dev_tools
    
    # Give services time to fully start
    log_info "Waiting for all services to be fully ready..."
    sleep 30
    
    verify_installation
    show_access_info
}

# Run main function
main "$@"