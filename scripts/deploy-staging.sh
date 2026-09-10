#!/bin/bash

# Sound Pesa Platform - Staging Deployment Script
# This script deploys the Sound Pesa platform to staging environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/soundpesa-staging"
COMPOSE_FILE="docker-compose.staging.yml"
BACKUP_DIR="/opt/soundpesa-staging/backups"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker and Docker Compose
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check required files
    local required_files=(
        ".env.staging"
        "docker-compose.staging.yml"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

# Create staging backup
create_backup() {
    log_info "Creating staging backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="staging_backup_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    mkdir -p "$backup_path"
    
    # Backup database if exists
    if docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        log_info "Backing up staging database..."
        docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U soundpesa soundpesa > "${backup_path}/database.sql" || log_warning "Database backup failed"
    fi
    
    # Backup configuration
    cp .env.staging "${backup_path}/"
    cp "$COMPOSE_FILE" "${backup_path}/"
    
    # Compress backup
    tar -czf "${backup_path}.tar.gz" -C "$BACKUP_DIR" "$backup_name"
    rm -rf "$backup_path"
    
    log_success "Staging backup created: ${backup_path}.tar.gz"
}

# Deploy to staging
deploy_staging() {
    log_info "Deploying to staging environment..."
    
    # Stop current services
    log_info "Stopping current staging services..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 30 || true
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build application images
    log_info "Building application images..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start core services
    log_info "Starting core services..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis vault
    
    # Wait for core services
    sleep 15
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" up -d api celery-worker celery-beat
    
    # Wait for API to be ready
    sleep 20
    
    # Run migrations
    log_info "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py migrate --noinput
    
    # Collect static files
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py collectstatic --noinput
    
    # Start remaining services
    log_info "Starting remaining services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Staging deployment completed"
}

# Run staging tests
run_tests() {
    log_info "Running staging tests..."
    
    # Wait for services to be ready
    sleep 30
    
    # Run API tests
    log_info "Running API tests..."
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py test --keepdb || log_warning "Some API tests failed"
    
    # Run integration tests
    log_info "Running integration tests..."
    
    # Test API health
    if curl -f -s http://localhost:8000/api/health/ >/dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Test database connectivity
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -d soundpesa -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "Database connectivity test passed"
    else
        log_error "Database connectivity test failed"
        return 1
    fi
    
    # Test Redis connectivity
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "Redis connectivity test passed"
    else
        log_error "Redis connectivity test failed"
        return 1
    fi
    
    # Test Celery workers
    if docker-compose -f "$COMPOSE_FILE" exec -T celery-worker celery -A sound_pesa inspect active >/dev/null 2>&1; then
        log_success "Celery workers test passed"
    else
        log_warning "Celery workers test failed"
    fi
    
    log_success "Staging tests completed"
}

# Load test data
load_test_data() {
    log_info "Loading test data..."
    
    # Create test users
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet
import uuid

User = get_user_model()

# Create test users
test_users = [
    {'username': 'testuser1', 'email': 'test1@staging.com', 'password': 'testpass123'},
    {'username': 'testuser2', 'email': 'test2@staging.com', 'password': 'testpass123'},
    {'username': 'testuser3', 'email': 'test3@staging.com', 'password': 'testpass123'},
]

for user_data in test_users:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        email=user_data['email'],
        defaults={'password': user_data['password']}
    )
    if created:
        user.set_password(user_data['password'])
        user.save()
        
        # Create wallets for each blockchain
        blockchains = ['bitcoin', 'ethereum', 'cardano', 'polkadot']
        for blockchain in blockchains:
            Wallet.objects.get_or_create(
                user=user,
                blockchain=blockchain,
                defaults={
                    'address': f'test_{blockchain}_address_{user.id}',
                    'encrypted_private_key': 'test_encrypted_key',
                }
            )
        print(f'Created test user: {user.username}')
    else:
        print(f'Test user already exists: {user.username}')
"
    
    log_success "Test data loaded"
}

# Performance tests
run_performance_tests() {
    log_info "Running performance tests..."
    
    # Simple load test using curl
    log_info "Testing API response times..."
    
    local endpoints=(
        "/api/health/"
        "/api/auth/login/"
        "/api/wallets/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local response_time=$(curl -o /dev/null -s -w '%{time_total}' "http://localhost:8000${endpoint}" || echo "0")
        log_info "Endpoint ${endpoint}: ${response_time}s"
        
        # Check if response time is acceptable (< 2 seconds)
        if (( $(echo "$response_time > 2.0" | bc -l) )); then
            log_warning "Slow response time for ${endpoint}: ${response_time}s"
        fi
    done
    
    log_success "Performance tests completed"
}

# Security tests
run_security_tests() {
    log_info "Running basic security tests..."
    
    # Test HTTPS redirect (if configured)
    log_info "Testing security headers..."
    
    # Test for common security headers
    local security_headers=$(curl -I -s http://localhost:8000/api/health/ | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)")
    
    if [ -n "$security_headers" ]; then
        log_success "Security headers found"
    else
        log_warning "Some security headers may be missing"
    fi
    
    # Test for exposed debug information
    if curl -s http://localhost:8000/api/health/ | grep -q "debug.*true"; then
        log_warning "Debug mode may be enabled in staging"
    fi
    
    log_success "Security tests completed"
}

# Generate staging report
generate_report() {
    log_info "Generating staging deployment report..."
    
    local report_file="staging_deployment_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Sound Pesa Staging Deployment Report
===================================
Deployment Date: $(date)
Environment: Staging

Service Status:
$(docker-compose -f "$COMPOSE_FILE" ps)

Container Resource Usage:
$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}")

API Health Check:
$(curl -s http://localhost:8000/api/health/ | jq . 2>/dev/null || echo "Health check failed")

Database Status:
$(docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -d soundpesa -c "SELECT version();" 2>/dev/null || echo "Database connection failed")

Test Results:
- API Health: $(curl -f -s http://localhost:8000/api/health/ >/dev/null 2>&1 && echo "PASS" || echo "FAIL")
- Database: $(docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -d soundpesa -c "SELECT 1;" >/dev/null 2>&1 && echo "PASS" || echo "FAIL")
- Redis: $(docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1 && echo "PASS" || echo "FAIL")

Access URLs:
- Web Application: http://staging.soundpesa.com
- API Documentation: http://staging-api.soundpesa.com/docs/
- Grafana Dashboard: http://staging-monitoring.soundpesa.com

Test Credentials:
- Username: testuser1, Password: testpass123
- Username: testuser2, Password: testpass123
- Username: testuser3, Password: testpass123

Notes:
- This is a staging environment using testnet blockchain connections
- All data is for testing purposes only
- Environment will be reset periodically
EOF
    
    log_success "Staging report generated: $report_file"
    
    # Display summary
    echo
    log_info "Staging Deployment Summary:"
    echo "  📊 Report: $report_file"
    echo "  🌐 Web App: http://staging.soundpesa.com"
    echo "  🔧 API Docs: http://staging-api.soundpesa.com/docs/"
    echo "  📈 Monitoring: http://staging-monitoring.soundpesa.com"
    echo "  👤 Test Users: testuser1, testuser2, testuser3 (password: testpass123)"
}

# Cleanup staging environment
cleanup_staging() {
    log_info "Cleaning up staging environment..."
    
    # Remove old containers and images
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    docker image prune -f
    docker volume prune -f
    docker network prune -f
    
    log_success "Staging cleanup completed"
}

# Main function
main() {
    echo "=========================================="
    echo "  Sound Pesa Staging Deployment"
    echo "=========================================="
    echo
    
    local start_time=$(date +%s)
    
    check_prerequisites
    create_backup
    deploy_staging
    run_tests
    load_test_data
    run_performance_tests
    run_security_tests
    generate_report
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Staging deployment completed successfully in ${duration} seconds!"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "test")
        run_tests
        ;;
    "cleanup")
        cleanup_staging
        ;;
    "report")
        generate_report
        ;;
    *)
        echo "Usage: $0 [deploy|test|cleanup|report]"
        echo "  deploy  - Full staging deployment (default)"
        echo "  test    - Run tests only"
        echo "  cleanup - Clean up staging environment"
        echo "  report  - Generate deployment report"
        exit 1
        ;;
esac