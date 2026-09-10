#!/bin/bash

# Sound Pesa Platform - Test Runner Script
# This script runs all tests across the platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"

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

# Test results
total_tests=0
passed_tests=0
failed_tests=0

# Run test suite
run_test_suite() {
    local service="$1"
    local command="$2"
    local description="$3"
    
    log_info "Running $description..."
    ((total_tests++))
    
    if docker compose -f "$COMPOSE_FILE" exec -T "$service" $command >/dev/null 2>&1; then
        log_success "$description passed"
        ((passed_tests++))
    else
        log_error "$description failed"
        ((failed_tests++))
    fi
}

# Main test execution
main() {
    echo "=========================================="
    echo "  Sound Pesa Platform Test Suite"
    echo "=========================================="
    echo
    
    # Check if services are running
    if ! docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_error "Services are not running. Please start them first with 'make dev'"
        exit 1
    fi
    
    # API Tests
    log_info "Testing API service..."
    if docker compose -f "$COMPOSE_FILE" ps api | grep -q "Up"; then
        run_test_suite "api" "python manage.py check" "API Health Check"
        # Uncomment when tests are implemented
        # run_test_suite "api" "python manage.py test" "API Unit Tests"
    else
        log_warning "API service not running, skipping API tests"
    fi
    
    # Web Tests
    log_info "Testing Web application..."
    if docker compose -f "$COMPOSE_FILE" ps web | grep -q "Up"; then
        # Uncomment when tests are implemented
        # run_test_suite "web" "npm test -- --run" "Web Unit Tests"
        log_info "Web tests not yet implemented"
    else
        log_warning "Web service not running, skipping web tests"
    fi
    
    # Mobile App Tests
    log_info "Testing Mobile application..."
    if docker compose -f "$COMPOSE_FILE" ps app | grep -q "Up"; then
        # Uncomment when tests are implemented
        # run_test_suite "app" "npm test" "Mobile App Tests"
        log_info "Mobile app tests not yet implemented"
    else
        log_warning "Mobile app service not running, skipping app tests"
    fi
    
    # Integration Tests
    log_info "Running integration tests..."
    
    # Test API health endpoint
    if curl -f -s http://localhost:8000/health/ >/dev/null 2>&1; then
        log_success "API health endpoint test passed"
        ((passed_tests++))
    else
        log_error "API health endpoint test failed"
        ((failed_tests++))
    fi
    ((total_tests++))
    
    # Test database connectivity
    if docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -d soundpesa -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "Database connectivity test passed"
        ((passed_tests++))
    else
        log_error "Database connectivity test failed"
        ((failed_tests++))
    fi
    ((total_tests++))
    
    # Test Redis connectivity
    if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "Redis connectivity test passed"
        ((passed_tests++))
    else
        log_error "Redis connectivity test failed"
        ((failed_tests++))
    fi
    ((total_tests++))
    
    # Show results
    echo
    echo "=========================================="
    echo "  Test Results Summary"
    echo "=========================================="
    echo
    echo "Total Tests: $total_tests"
    echo -e "Passed:      ${GREEN}$passed_tests${NC}"
    echo -e "Failed:      ${RED}$failed_tests${NC}"
    echo
    
    if [ $failed_tests -eq 0 ]; then
        echo -e "Overall Status: ${GREEN}ALL TESTS PASSED${NC} ✓"
        exit 0
    else
        echo -e "Overall Status: ${RED}SOME TESTS FAILED${NC} ✗"
        exit 1
    fi
}

# Run main function
main "$@"