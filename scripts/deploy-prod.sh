#!/bin/bash

# Sound Pesa Platform - Production Deployment Script
# This script deploys the Sound Pesa platform to production environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/opt/soundpesa/backups"
DEPLOY_DIR="/opt/soundpesa"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_RETENTION_DAYS=30

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

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Validate environment
validate_environment() {
    log_info "Validating production environment..."
    
    # Check required files
    local required_files=(
        ".env.prod"
        "docker-compose.prod.yml"
        "packages/api/.env.prod"
        "packages/web/.env.prod"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
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
    
    # Validate compose file
    if ! docker-compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
        log_error "Invalid Docker Compose configuration"
        exit 1
    fi
    
    log_success "Environment validation passed"
}

# Create backup
create_backup() {
    log_info "Creating backup before deployment..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="soundpesa_backup_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    # Create backup directory
    mkdir -p "$backup_path"
    
    # Backup database
    log_info "Backing up database..."
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U soundpesa soundpesa > "${backup_path}/database.sql"
    
    # Backup Vault data
    log_info "Backing up Vault data..."
    docker-compose -f "$COMPOSE_FILE" exec -T vault vault operator raft snapshot save /vault/data/backup.snap || log_warning "Vault backup failed"
    docker cp $(docker-compose -f "$COMPOSE_FILE" ps -q vault):/vault/data/backup.snap "${backup_path}/vault_backup.snap" || log_warning "Could not copy Vault backup"
    
    # Backup configuration files
    log_info "Backing up configuration files..."
    cp -r docker/ "${backup_path}/"
    cp .env.prod "${backup_path}/"
    cp "$COMPOSE_FILE" "${backup_path}/"
    
    # Backup application data
    if [ -d "/opt/soundpesa/data" ]; then
        log_info "Backing up application data..."
        cp -r /opt/soundpesa/data "${backup_path}/"
    fi
    
    # Compress backup
    log_info "Compressing backup..."
    tar -czf "${backup_path}.tar.gz" -C "$BACKUP_DIR" "$backup_name"
    rm -rf "$backup_path"
    
    log_success "Backup created: ${backup_path}.tar.gz"
    
    # Clean old backups
    find "$BACKUP_DIR" -name "soundpesa_backup_*.tar.gz" -mtime +$BACKUP_RETENTION_DAYS -delete
    log_info "Cleaned backups older than $BACKUP_RETENTION_DAYS days"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check disk space
    local available_space=$(df / | awk 'NR==2 {print $4}')
    local required_space=5000000  # 5GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_error "Insufficient disk space. Available: ${available_space}KB, Required: ${required_space}KB"
        exit 1
    fi
    
    # Check memory
    local available_memory=$(free | awk 'NR==2{printf "%.0f", $7/1024}')
    local required_memory=2048  # 2GB in MB
    
    if [ "$available_memory" -lt "$required_memory" ]; then
        log_warning "Low available memory. Available: ${available_memory}MB, Recommended: ${required_memory}MB"
    fi
    
    # Check if services are healthy
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "Checking current service health..."
        
        # Check API health
        if curl -f -s http://localhost:8000/api/health/ >/dev/null 2>&1; then
            log_info "Current API is healthy"
        else
            log_warning "Current API health check failed"
        fi
    fi
    
    log_success "Pre-deployment checks completed"
}

# Pull latest images
pull_images() {
    log_info "Pulling latest Docker images..."
    
    # Pull base images
    docker-compose -f "$COMPOSE_FILE" pull
    
    log_success "Docker images pulled successfully"
}

# Build application images
build_images() {
    log_info "Building application images..."
    
    # Build with no cache to ensure latest code
    docker-compose -f "$COMPOSE_FILE" build --no-cache --parallel
    
    log_success "Application images built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Stop current services gracefully
    log_info "Stopping current services..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 30
    
    # Start core services first
    log_info "Starting core services..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis vault
    
    # Wait for core services
    log_info "Waiting for core services to be ready..."
    sleep 15
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" up -d api celery-worker celery-beat
    
    # Wait for application services
    log_info "Waiting for application services to be ready..."
    sleep 20
    
    # Start frontend services
    log_info "Starting frontend services..."
    docker-compose -f "$COMPOSE_FILE" up -d web nginx
    
    # Start monitoring services
    log_info "Starting monitoring services..."
    docker-compose -f "$COMPOSE_FILE" up -d prometheus grafana loki promtail alertmanager
    
    # Start blockchain services
    log_info "Starting blockchain services..."
    docker-compose -f "$COMPOSE_FILE" up -d bitcoin-core geth prysm-beacon cardano-node polkadot
    
    log_success "Services deployed successfully"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for API to be fully ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py check --database default >/dev/null 2>&1; then
            break
        fi
        
        log_info "Waiting for database connection... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Database connection timeout"
        exit 1
    fi
    
    # Run migrations
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py migrate --noinput
    
    # Collect static files
    log_info "Collecting static files..."
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py collectstatic --noinput
    
    log_success "Database migrations completed"
}

# Post-deployment verification
verify_deployment() {
    log_info "Verifying deployment..."
    
    local failed_checks=()
    local max_attempts=10
    local attempt=1
    
    # Wait for services to be fully ready
    sleep 30
    
    # Check service status
    log_info "Checking service status..."
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        failed_checks+=("Some services are not running")
    fi
    
    # Check API health
    log_info "Checking API health..."
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8000/api/health/ >/dev/null 2>&1; then
            log_success "API health check passed"
            break
        fi
        
        log_info "API health check attempt $attempt/$max_attempts..."
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        failed_checks+=("API health check failed")
    fi
    
    # Check web application
    log_info "Checking web application..."
    if ! curl -f -s http://localhost:3000 >/dev/null 2>&1; then
        failed_checks+=("Web application not accessible")
    fi
    
    # Check database connectivity
    log_info "Checking database connectivity..."
    if ! docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -d soundpesa -c "SELECT 1;" >/dev/null 2>&1; then
        failed_checks+=("Database connection failed")
    fi
    
    # Check Redis connectivity
    log_info "Checking Redis connectivity..."
    if ! docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
        failed_checks+=("Redis connection failed")
    fi
    
    # Check Celery workers
    log_info "Checking Celery workers..."
    if ! docker-compose -f "$COMPOSE_FILE" exec -T celery-worker celery -A sound_pesa inspect active >/dev/null 2>&1; then
        failed_checks+=("Celery workers not responding")
    fi
    
    # Report results
    if [ ${#failed_checks[@]} -ne 0 ]; then
        log_error "Deployment verification failed:"
        for check in "${failed_checks[@]}"; do
            log_error "  - $check"
        done
        
        log_info "Check logs for more details:"
        log_info "  docker-compose -f $COMPOSE_FILE logs"
        exit 1
    else
        log_success "All deployment verification checks passed!"
    fi
}

# Setup monitoring alerts
setup_monitoring() {
    log_info "Setting up monitoring and alerts..."
    
    # Wait for Prometheus to be ready
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:9090/-/ready >/dev/null 2>&1; then
            break
        fi
        
        log_info "Waiting for Prometheus... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    # Configure Grafana datasources and dashboards
    if curl -f -s http://localhost:3001/api/health >/dev/null 2>&1; then
        log_info "Grafana is ready"
        # Grafana will auto-provision datasources and dashboards from config
    else
        log_warning "Grafana is not ready, monitoring setup may be incomplete"
    fi
    
    log_success "Monitoring setup completed"
}

# Cleanup old resources
cleanup_old_resources() {
    log_info "Cleaning up old Docker resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful in production)
    # docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    log_success "Cleanup completed"
}

# Send deployment notification
send_notification() {
    local status=$1
    local message=$2
    
    # Add your notification logic here (Slack, email, etc.)
    log_info "Deployment notification: $status - $message"
    
    # Example: Send to Slack webhook
    # curl -X POST -H 'Content-type: application/json' \
    #   --data "{\"text\":\"Sound Pesa Deployment: $status - $message\"}" \
    #   "$SLACK_WEBHOOK_URL"
}

# Rollback function
rollback() {
    log_error "Deployment failed. Initiating rollback..."
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Find latest backup
    local latest_backup=$(ls -t "${BACKUP_DIR}"/soundpesa_backup_*.tar.gz 2>/dev/null | head -1)
    
    if [ -n "$latest_backup" ]; then
        log_info "Rolling back to: $latest_backup"
        
        # Extract backup
        local backup_name=$(basename "$latest_backup" .tar.gz)
        tar -xzf "$latest_backup" -C "$BACKUP_DIR"
        
        # Restore database
        docker-compose -f "$COMPOSE_FILE" up -d postgres
        sleep 10
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -c "DROP DATABASE IF EXISTS soundpesa;"
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -c "CREATE DATABASE soundpesa;"
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa soundpesa < "${BACKUP_DIR}/${backup_name}/database.sql"
        
        # Start services with previous configuration
        cp "${BACKUP_DIR}/${backup_name}/docker-compose.prod.yml" .
        docker-compose -f "$COMPOSE_FILE" up -d
        
        log_success "Rollback completed"
        send_notification "ROLLBACK" "Deployment rolled back to $backup_name"
    else
        log_error "No backup found for rollback"
        send_notification "ROLLBACK_FAILED" "No backup available for rollback"
    fi
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    echo "=========================================="
    echo "  Sound Pesa Production Deployment"
    echo "=========================================="
    echo
    
    # Set up error handling
    trap 'rollback' ERR
    
    check_permissions
    validate_environment
    create_backup
    pre_deployment_checks
    pull_images
    build_images
    deploy_services
    run_migrations
    verify_deployment
    setup_monitoring
    cleanup_old_resources
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Production deployment completed successfully in ${duration} seconds!"
    
    echo
    log_info "Production URLs:"
    echo "  🌐 Web Application:     https://soundpesa.com"
    echo "  🔧 API Documentation:  https://api.soundpesa.com/docs/"
    echo "  📊 Grafana Dashboard:  https://monitoring.soundpesa.com"
    echo "  📈 Prometheus:         https://prometheus.soundpesa.com"
    echo
    log_info "Monitoring and logs:"
    echo "  View logs:           docker-compose -f $COMPOSE_FILE logs -f"
    echo "  Service status:      docker-compose -f $COMPOSE_FILE ps"
    echo "  System metrics:      https://monitoring.soundpesa.com"
    echo
    
    send_notification "SUCCESS" "Production deployment completed in ${duration} seconds"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    "verify")
        verify_deployment
        ;;
    "backup")
        create_backup
        ;;
    *)
        echo "Usage: $0 [deploy|rollback|verify|backup]"
        echo "  deploy   - Full production deployment (default)"
        echo "  rollback - Rollback to previous version"
        echo "  verify   - Verify current deployment"
        echo "  backup   - Create backup only"
        exit 1
        ;;
esac