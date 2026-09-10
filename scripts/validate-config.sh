#!/bin/bash

# Sound Pesa Platform - Configuration Validation Script
# This script validates environment configuration files and settings

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-development}"
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

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

# Validation results
declare -A validation_results
total_checks=0
passed_checks=0
failed_checks=0
warning_checks=0

# Record validation result
record_result() {
    local check="$1"
    local status="$2"
    local message="$3"
    
    validation_results["$check"]="$status:$message"
    ((total_checks++))
    
    case "$status" in
        "PASS")
            ((passed_checks++))
            log_success "$check: $message"
            ;;
        "FAIL")
            ((failed_checks++))
            log_error "$check: $message"
            ;;
        "WARN")
            ((warning_checks++))
            log_warning "$check: $message"
            ;;
    esac
}

# Check if file exists
check_file_exists() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        record_result "$description" "PASS" "File exists: $file"
        return 0
    else
        record_result "$description" "FAIL" "File missing: $file"
        return 1
    fi
}

# Check environment variable in file
check_env_var() {
    local file="$1"
    local var="$2"
    local description="$3"
    local required="${4:-true}"
    
    if [ ! -f "$file" ]; then
        record_result "$description" "FAIL" "Configuration file not found: $file"
        return 1
    fi
    
    if grep -q "^${var}=" "$file"; then
        local value=$(grep "^${var}=" "$file" | cut -d'=' -f2- | sed 's/^"//' | sed 's/"$//')
        
        if [ -z "$value" ] || [ "$value" = "change_me" ] || [ "$value" = "your-value-here" ]; then
            if [ "$required" = "true" ]; then
                record_result "$description" "FAIL" "$var is empty or has placeholder value"
            else
                record_result "$description" "WARN" "$var is empty or has placeholder value (optional)"
            fi
        else
            record_result "$description" "PASS" "$var is configured"
        fi
    else
        if [ "$required" = "true" ]; then
            record_result "$description" "FAIL" "$var is not defined in $file"
        else
            record_result "$description" "WARN" "$var is not defined in $file (optional)"
        fi
    fi
}

# Check password strength
check_password_strength() {
    local file="$1"
    local var="$2"
    local description="$3"
    
    if [ ! -f "$file" ]; then
        record_result "$description" "FAIL" "Configuration file not found: $file"
        return 1
    fi
    
    if grep -q "^${var}=" "$file"; then
        local password=$(grep "^${var}=" "$file" | cut -d'=' -f2- | sed 's/^"//' | sed 's/"$//')
        
        # Check for common weak passwords
        local weak_passwords=("password" "123456" "admin" "root" "test" "dev" "change_me" "your-password-here")
        
        for weak in "${weak_passwords[@]}"; do
            if [[ "$password" == *"$weak"* ]]; then
                record_result "$description" "FAIL" "$var contains weak password pattern: $weak"
                return 1
            fi
        done
        
        # Check password length
        if [ ${#password} -lt 12 ]; then
            record_result "$description" "WARN" "$var is shorter than 12 characters"
        elif [ ${#password} -lt 8 ]; then
            record_result "$description" "FAIL" "$var is shorter than 8 characters"
        else
            record_result "$description" "PASS" "$var has adequate length"
        fi
    else
        record_result "$description" "FAIL" "$var is not defined in $file"
    fi
}

# Check URL format
check_url_format() {
    local file="$1"
    local var="$2"
    local description="$3"
    
    if [ ! -f "$file" ]; then
        record_result "$description" "FAIL" "Configuration file not found: $file"
        return 1
    fi
    
    if grep -q "^${var}=" "$file"; then
        local url=$(grep "^${var}=" "$file" | cut -d'=' -f2- | sed 's/^"//' | sed 's/"$//')
        
        if [[ "$url" =~ ^https?://[a-zA-Z0-9.-]+:[0-9]+$ ]] || [[ "$url" =~ ^https?://[a-zA-Z0-9.-]+$ ]]; then
            record_result "$description" "PASS" "$var has valid URL format"
        else
            record_result "$description" "FAIL" "$var has invalid URL format: $url"
        fi
    else
        record_result "$description" "FAIL" "$var is not defined in $file"
    fi
}

# Check Docker Compose file
check_docker_compose() {
    log_info "Validating Docker Compose configuration..."
    
    check_file_exists "$COMPOSE_FILE" "Docker Compose File"
    
    if [ -f "$COMPOSE_FILE" ]; then
        # Validate Docker Compose syntax
        if docker-compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
            record_result "Docker Compose Syntax" "PASS" "Syntax is valid"
        else
            record_result "Docker Compose Syntax" "FAIL" "Syntax validation failed"
        fi
        
        # Check for required services
        local required_services=("api" "postgres" "redis" "vault")
        for service in "${required_services[@]}"; do
            if docker-compose -f "$COMPOSE_FILE" config | grep -q "^  $service:"; then
                record_result "Service-$service" "PASS" "Service is defined"
            else
                record_result "Service-$service" "FAIL" "Service is not defined"
            fi
        done
    fi
}

# Check main environment file
check_main_env() {
    log_info "Validating main environment configuration..."
    
    local env_file=".env"
    if [ "$ENVIRONMENT" != "development" ]; then
        env_file=".env.${ENVIRONMENT}"
    fi
    
    check_file_exists "$env_file" "Main Environment File"
    
    if [ -f "$env_file" ]; then
        # Check required variables
        check_env_var "$env_file" "COMPOSE_PROJECT_NAME" "Project Name"
        check_env_var "$env_file" "ENVIRONMENT" "Environment Type"
        
        # Check database configuration
        check_env_var "$env_file" "POSTGRES_DB" "Database Name"
        check_env_var "$env_file" "POSTGRES_USER" "Database User"
        check_password_strength "$env_file" "POSTGRES_PASSWORD" "Database Password"
        
        # Check Redis configuration
        check_password_strength "$env_file" "REDIS_PASSWORD" "Redis Password"
        
        # Check API configuration
        check_password_strength "$env_file" "DJANGO_SECRET_KEY" "Django Secret Key"
        check_password_strength "$env_file" "JWT_SECRET_KEY" "JWT Secret Key"
        
        # Check Vault configuration
        if [ "$ENVIRONMENT" = "production" ]; then
            check_password_strength "$env_file" "VAULT_TOKEN" "Vault Token"
        fi
        
        # Check blockchain configuration
        check_env_var "$env_file" "BITCOIN_NETWORK" "Bitcoin Network"
        check_env_var "$env_file" "ETHEREUM_NETWORK" "Ethereum Network"
        
        # Check monitoring configuration
        if [ "$ENVIRONMENT" != "development" ]; then
            check_password_strength "$env_file" "GRAFANA_ADMIN_PASSWORD" "Grafana Password"
        fi
    fi
}

# Check API environment file
check_api_env() {
    log_info "Validating API environment configuration..."
    
    local api_env_file="packages/api/.env"
    if [ "$ENVIRONMENT" != "development" ]; then
        api_env_file="packages/api/.env.${ENVIRONMENT}"
    fi
    
    check_file_exists "$api_env_file" "API Environment File"
    
    if [ -f "$api_env_file" ]; then
        # Check Django configuration
        check_env_var "$api_env_file" "DEBUG" "Debug Mode"
        check_password_strength "$api_env_file" "SECRET_KEY" "Django Secret Key"
        check_env_var "$api_env_file" "ALLOWED_HOSTS" "Allowed Hosts"
        
        # Check database URL
        check_url_format "$api_env_file" "DATABASE_URL" "Database URL"
        
        # Check Redis URL
        check_url_format "$api_env_file" "REDIS_URL" "Redis URL"
        
        # Check Vault configuration
        check_url_format "$api_env_file" "VAULT_URL" "Vault URL"
        
        # Check blockchain RPC URLs
        check_url_format "$api_env_file" "BITCOIN_RPC_URL" "Bitcoin RPC URL"
        check_url_format "$api_env_file" "ETHEREUM_RPC_URL" "Ethereum RPC URL"
        
        # Check JWT configuration
        check_password_strength "$api_env_file" "JWT_SECRET_KEY" "JWT Secret Key"
        
        # Check CORS configuration
        check_env_var "$api_env_file" "CORS_ALLOWED_ORIGINS" "CORS Origins"
    fi
}

# Check web environment file
check_web_env() {
    log_info "Validating web environment configuration..."
    
    local web_env_file="packages/web/.env.local"
    if [ "$ENVIRONMENT" != "development" ]; then
        web_env_file="packages/web/.env.${ENVIRONMENT}"
    fi
    
    check_file_exists "$web_env_file" "Web Environment File"
    
    if [ -f "$web_env_file" ]; then
        # Check API URLs
        check_url_format "$web_env_file" "NEXT_PUBLIC_API_URL" "API URL"
        
        # Check NextAuth configuration
        check_url_format "$web_env_file" "NEXTAUTH_URL" "NextAuth URL"
        check_password_strength "$web_env_file" "NEXTAUTH_SECRET" "NextAuth Secret"
        
        # Check PWA configuration
        check_env_var "$web_env_file" "NEXT_PUBLIC_PWA_NAME" "PWA Name"
        
        # Check feature flags
        check_env_var "$web_env_file" "NEXT_PUBLIC_ENABLE_BITCOIN" "Bitcoin Feature" "false"
        check_env_var "$web_env_file" "NEXT_PUBLIC_ENABLE_ETHEREUM" "Ethereum Feature" "false"
    fi
}

# Check mobile app environment file
check_app_env() {
    log_info "Validating mobile app environment configuration..."
    
    local app_env_file="packages/app/.env"
    if [ "$ENVIRONMENT" != "development" ]; then
        app_env_file="packages/app/.env.${ENVIRONMENT}"
    fi
    
    check_file_exists "$app_env_file" "Mobile App Environment File"
    
    if [ -f "$app_env_file" ]; then
        # Check API URLs
        check_url_format "$app_env_file" "EXPO_PUBLIC_API_URL" "API URL"
        
        # Check app configuration
        check_env_var "$app_env_file" "EXPO_PUBLIC_APP_NAME" "App Name"
        check_env_var "$app_env_file" "EXPO_PUBLIC_APP_VERSION" "App Version"
        
        # Check bundle IDs
        check_env_var "$app_env_file" "EXPO_PUBLIC_IOS_BUNDLE_ID" "iOS Bundle ID"
        check_env_var "$app_env_file" "EXPO_PUBLIC_ANDROID_PACKAGE" "Android Package"
        
        # Check feature flags
        check_env_var "$app_env_file" "EXPO_PUBLIC_ENABLE_BIOMETRIC_AUTH" "Biometric Auth" "false"
        check_env_var "$app_env_file" "EXPO_PUBLIC_ENABLE_PUSH_NOTIFICATIONS" "Push Notifications" "false"
    fi
}

# Check security configuration
check_security_config() {
    log_info "Validating security configuration..."
    
    # Check for production security settings
    if [ "$ENVIRONMENT" = "production" ]; then
        local main_env=".env.production"
        
        if [ -f "$main_env" ]; then
            # Check SSL settings
            if grep -q "SECURE_SSL_REDIRECT=true" "$main_env"; then
                record_result "SSL Redirect" "PASS" "SSL redirect is enabled"
            else
                record_result "SSL Redirect" "FAIL" "SSL redirect should be enabled in production"
            fi
            
            # Check HSTS settings
            if grep -q "SECURE_HSTS_SECONDS=[1-9]" "$main_env"; then
                record_result "HSTS" "PASS" "HSTS is configured"
            else
                record_result "HSTS" "FAIL" "HSTS should be configured in production"
            fi
            
            # Check debug mode
            if grep -q "DJANGO_DEBUG=false" "$main_env"; then
                record_result "Debug Mode" "PASS" "Debug mode is disabled"
            else
                record_result "Debug Mode" "FAIL" "Debug mode should be disabled in production"
            fi
        fi
    fi
    
    # Check for default/weak passwords
    local config_files=(".env" ".env.${ENVIRONMENT}" "packages/api/.env" "packages/web/.env.local" "packages/app/.env")
    
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            # Check for placeholder values
            if grep -q "change.*me\|your.*here\|example\|test.*password" "$file"; then
                record_result "Placeholder Values" "WARN" "Found placeholder values in $file"
            fi
            
            # Check for hardcoded secrets in production
            if [ "$ENVIRONMENT" = "production" ] && grep -q "dev.*secret\|test.*key\|localhost" "$file"; then
                record_result "Production Secrets" "FAIL" "Found development values in production config: $file"
            fi
        fi
    done
}

# Check network configuration
check_network_config() {
    log_info "Validating network configuration..."
    
    # Check blockchain networks
    local main_env=".env"
    if [ "$ENVIRONMENT" != "development" ]; then
        main_env=".env.${ENVIRONMENT}"
    fi
    
    if [ -f "$main_env" ]; then
        # Check if using appropriate networks for environment
        if [ "$ENVIRONMENT" = "production" ]; then
            if grep -q "BITCOIN_NETWORK=mainnet" "$main_env"; then
                record_result "Bitcoin Network" "PASS" "Using mainnet for production"
            else
                record_result "Bitcoin Network" "WARN" "Consider using mainnet for production"
            fi
            
            if grep -q "ETHEREUM_NETWORK=mainnet" "$main_env"; then
                record_result "Ethereum Network" "PASS" "Using mainnet for production"
            else
                record_result "Ethereum Network" "WARN" "Consider using mainnet for production"
            fi
        else
            if grep -q "BITCOIN_NETWORK=testnet" "$main_env"; then
                record_result "Bitcoin Network" "PASS" "Using testnet for development/staging"
            else
                record_result "Bitcoin Network" "WARN" "Consider using testnet for development/staging"
            fi
        fi
    fi
}

# Check resource configuration
check_resource_config() {
    log_info "Validating resource configuration..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        # Check if resource limits are defined for production
        if [ "$ENVIRONMENT" = "production" ]; then
            if grep -q "resources:" "$COMPOSE_FILE"; then
                record_result "Resource Limits" "PASS" "Resource limits are defined"
            else
                record_result "Resource Limits" "WARN" "Consider defining resource limits for production"
            fi
        fi
        
        # Check for health checks
        if grep -q "healthcheck:" "$COMPOSE_FILE"; then
            record_result "Health Checks" "PASS" "Health checks are configured"
        else
            record_result "Health Checks" "WARN" "Consider adding health checks to services"
        fi
        
        # Check for restart policies
        if grep -q "restart:" "$COMPOSE_FILE"; then
            record_result "Restart Policies" "PASS" "Restart policies are configured"
        else
            record_result "Restart Policies" "WARN" "Consider adding restart policies to services"
        fi
    fi
}

# Generate validation report
generate_report() {
    local report_file="config_validation_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Sound Pesa Platform Configuration Validation Report
==================================================
Environment: $ENVIRONMENT
Generated: $(date)

Summary:
--------
Total Checks: $total_checks
Passed: $passed_checks
Warnings: $warning_checks
Failed: $failed_checks

Overall Status: $([ $failed_checks -eq 0 ] && echo "VALID" || echo "INVALID")

Detailed Results:
----------------
EOF
    
    for check in "${!validation_results[@]}"; do
        local result="${validation_results[$check]}"
        local status="${result%%:*}"
        local message="${result#*:}"
        echo "$check: [$status] $message" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF

Recommendations:
---------------
EOF
    
    if [ $failed_checks -gt 0 ]; then
        echo "1. Fix all FAILED checks before deploying to $ENVIRONMENT" >> "$report_file"
    fi
    
    if [ $warning_checks -gt 0 ]; then
        echo "2. Review and address WARNING items for better security and reliability" >> "$report_file"
    fi
    
    if [ "$ENVIRONMENT" = "production" ]; then
        cat >> "$report_file" << EOF
3. Ensure all passwords and secrets are strong and unique
4. Enable SSL/TLS for all external communications
5. Configure proper firewall rules and network security
6. Set up monitoring and alerting for all critical services
7. Implement regular backup and disaster recovery procedures
8. Keep all software and dependencies up to date
EOF
    fi
    
    echo "$report_file"
}

# Show summary
show_summary() {
    echo
    echo "=========================================="
    echo "  Configuration Validation Summary"
    echo "=========================================="
    echo
    echo "Environment: $ENVIRONMENT"
    echo "Total Checks: $total_checks"
    echo -e "Passed:       ${GREEN}$passed_checks${NC}"
    echo -e "Warnings:     ${YELLOW}$warning_checks${NC}"
    echo -e "Failed:       ${RED}$failed_checks${NC}"
    echo
    
    if [ $failed_checks -eq 0 ]; then
        if [ $warning_checks -eq 0 ]; then
            echo -e "Overall Status: ${GREEN}VALID${NC} ✓"
        else
            echo -e "Overall Status: ${YELLOW}VALID WITH WARNINGS${NC} ⚠"
        fi
    else
        echo -e "Overall Status: ${RED}INVALID${NC} ✗"
    fi
    
    echo
    
    if [ $failed_checks -gt 0 ]; then
        echo "Critical issues that must be fixed:"
        for check in "${!validation_results[@]}"; do
            local result="${validation_results[$check]}"
            local status="${result%%:*}"
            local message="${result#*:}"
            if [ "$status" = "FAIL" ]; then
                echo -e "  ${RED}✗${NC} $check: $message"
            fi
        done
        echo
    fi
    
    if [ $warning_checks -gt 0 ]; then
        echo "Warnings to consider:"
        for check in "${!validation_results[@]}"; do
            local result="${validation_results[$check]}"
            local status="${result%%:*}"
            local message="${result#*:}"
            if [ "$status" = "WARN" ]; then
                echo -e "  ${YELLOW}⚠${NC} $check: $message"
            fi
        done
        echo
    fi
}

# Main validation function
main() {
    echo "=========================================="
    echo "  Sound Pesa Configuration Validation"
    echo "=========================================="
    echo
    echo "Environment: $ENVIRONMENT"
    echo
    
    check_docker_compose
    check_main_env
    check_api_env
    check_web_env
    check_app_env
    check_security_config
    check_network_config
    check_resource_config
    
    show_summary
    
    # Generate report if requested
    if [ "${2:-}" = "--report" ]; then
        local report_file=$(generate_report)
        echo "Validation report generated: $report_file"
    fi
    
    # Exit with error code if there are failures
    if [ $failed_checks -gt 0 ]; then
        exit 1
    fi
}

# Show help
show_help() {
    echo "Sound Pesa Configuration Validation Script"
    echo
    echo "Usage: $0 <environment> [--report]"
    echo
    echo "Environments:"
    echo "  development - Validate development configuration"
    echo "  staging     - Validate staging configuration"
    echo "  production  - Validate production configuration"
    echo
    echo "Options:"
    echo "  --report    - Generate detailed validation report"
    echo
    echo "Examples:"
    echo "  $0 development"
    echo "  $0 production --report"
}

# Handle command line arguments
case "${1:-development}" in
    "development"|"staging"|"production")
        main "$@"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        log_error "Invalid environment: $1"
        show_help
        exit 1
        ;;
esac