#!/bin/bash

# Sound Pesa Platform - Health Check Script
# This script checks the health of all services

# set -e  # Don't exit on error for health checks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
REPORT_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --report)
            REPORT_MODE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Health check results
total_checks=0
passed_checks=0
failed_checks=0

# Check service health
check_service_health() {
    local service="$1"
    local description="$2"
    local health_command="$3"
    
    ((total_checks++))
    
    if docker compose -f "$COMPOSE_FILE" ps "$service" 2>/dev/null | grep -q "Up"; then
        if [ -n "$health_command" ]; then
            if eval "$health_command" >/dev/null 2>&1; then
                log_success "$description is healthy"
                ((passed_checks++))
            else
                log_error "$description is unhealthy"
                ((failed_checks++))
            fi
        else
            log_success "$description is running"
            ((passed_checks++))
        fi
    else
        log_error "$description is not running"
        ((failed_checks++))
    fi
}

# Check URL endpoint
check_url() {
    local url="$1"
    local description="$2"
    
    ((total_checks++))
    
    if curl -f -s "$url" >/dev/null 2>&1; then
        log_success "$description endpoint is accessible"
        ((passed_checks++))
    else
        log_error "$description endpoint is not accessible"
        ((failed_checks++))
    fi
}

# Main health check
main() {
    echo "=========================================="
    echo "  Sound Pesa Platform Health Check"
    echo "=========================================="
    echo
    
    # Core Services
    log_info "Checking core services..."
    check_service_health "postgres" "PostgreSQL Database" "docker compose -f $COMPOSE_FILE exec -T postgres pg_isready -U soundpesa"
    check_service_health "redis" "Redis Cache" "docker compose -f $COMPOSE_FILE exec -T redis redis-cli ping"
    check_service_health "vault" "HashiCorp Vault" "docker compose -f $COMPOSE_FILE exec -T vault vault status"
    
    # Application Services
    log_info "Checking application services..."
    check_service_health "api" "Django API" "docker compose -f $COMPOSE_FILE exec -T api python manage.py check"
    check_service_health "web" "Next.js Web App"
    check_service_health "app" "React Native App"
    
    # Background Services
    log_info "Checking background services..."
    check_service_health "celery-worker" "Celery Worker" "docker compose -f $COMPOSE_FILE exec -T celery-worker celery -A sound_pesa inspect ping"
    check_service_health "celery-beat" "Celery Beat Scheduler"
    
    # Monitoring Services
    log_info "Checking monitoring services..."
    check_service_health "prometheus" "Prometheus"
    check_service_health "grafana" "Grafana"
    check_service_health "loki" "Loki"
    check_service_health "promtail" "Promtail"
    
    # HTTP Endpoints
    log_info "Checking HTTP endpoints..."
    check_url "http://localhost:8000/health/" "API Health"
    check_url "http://localhost:3000" "Web Application"
    check_url "http://localhost:3001" "Grafana Dashboard"
    check_url "http://localhost:9090" "Prometheus"
    
    # Development-only services
    if [[ "$COMPOSE_FILE" == *"dev"* ]]; then
        log_info "Checking development services..."
        check_service_health "mailhog" "Mailhog"
        check_url "http://localhost:8025" "Mailhog UI"
    fi
    
    # Show results
    echo
    echo "=========================================="
    echo "  Health Check Summary"
    echo "=========================================="
    echo
    echo "Total Checks: $total_checks"
    echo -e "Passed:       ${GREEN}$passed_checks${NC}"
    echo -e "Failed:       ${RED}$failed_checks${NC}"
    echo
    
    if [ $failed_checks -eq 0 ]; then
        echo -e "Overall Health: ${GREEN}HEALTHY${NC} ✓"
        exit_code=0
    else
        echo -e "Overall Health: ${RED}UNHEALTHY${NC} ✗"
        exit_code=1
    fi
    
    # Generate detailed report if requested
    if [ "$REPORT_MODE" = true ]; then
        echo
        echo "=========================================="
        echo "  Detailed Health Report"
        echo "=========================================="
        echo
        
        # Container status
        echo "Container Status:"
        docker compose -f "$COMPOSE_FILE" ps
        echo
        
        # Resource usage
        echo "Resource Usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
        echo
        
        # Disk usage
        echo "Docker Disk Usage:"
        docker system df
        echo
        
        # Network status
        echo "Network Status:"
        docker network ls
        echo
        
        # Volume status
        echo "Volume Status:"
        docker volume ls
        echo
    fi
    
    exit $exit_code
}

# Run main function
main "$@"