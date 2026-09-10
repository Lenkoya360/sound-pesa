#!/bin/bash

# Sound Pesa Platform - Database Migration Script
# This script handles database migrations and schema management

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
BACKUP_DIR="./backups/migrations"

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

# Check if API service is running
check_api_service() {
    if ! docker-compose -f "$COMPOSE_FILE" ps api | grep -q "Up"; then
        log_error "API service is not running. Please start it first:"
        log_info "  docker-compose -f $COMPOSE_FILE up -d api"
        exit 1
    fi
}

# Create migration backup
create_migration_backup() {
    log_info "Creating migration backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/migration_backup_${timestamp}.sql"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current database state
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U soundpesa soundpesa > "$backup_file"
    
    log_success "Migration backup created: $backup_file"
}

# Show migration status
show_migration_status() {
    log_info "Current migration status:"
    echo
    docker-compose -f "$COMPOSE_FILE" exec api python manage.py showmigrations
    echo
}

# Check for migration conflicts
check_migration_conflicts() {
    log_info "Checking for migration conflicts..."
    
    local conflicts=$(docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py showmigrations | grep -c "\[ \].*\[X\]" || true)
    
    if [ "$conflicts" -gt 0 ]; then
        log_error "Migration conflicts detected!"
        log_info "Run 'python manage.py showmigrations' to see details"
        log_info "Use 'python manage.py makemigrations --merge' to resolve conflicts"
        return 1
    fi
    
    log_success "No migration conflicts found"
}

# Create new migrations
make_migrations() {
    local app_name="${1:-}"
    
    log_info "Creating new migrations..."
    
    if [ -n "$app_name" ]; then
        log_info "Creating migrations for app: $app_name"
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py makemigrations "$app_name"
    else
        log_info "Creating migrations for all apps"
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py makemigrations
    fi
    
    log_success "Migrations created successfully"
}

# Run migrations
run_migrations() {
    local app_name="${1:-}"
    local migration_name="${2:-}"
    
    log_info "Running database migrations..."
    
    # Check database connectivity first
    if ! docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py check --database default >/dev/null 2>&1; then
        log_error "Database connection failed"
        exit 1
    fi
    
    if [ -n "$app_name" ] && [ -n "$migration_name" ]; then
        log_info "Running specific migration: $app_name.$migration_name"
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py migrate "$app_name" "$migration_name"
    elif [ -n "$app_name" ]; then
        log_info "Running migrations for app: $app_name"
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py migrate "$app_name"
    else
        log_info "Running all pending migrations"
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py migrate
    fi
    
    log_success "Migrations completed successfully"
}

# Fake migration (mark as applied without running)
fake_migration() {
    local app_name="$1"
    local migration_name="$2"
    
    if [ -z "$app_name" ] || [ -z "$migration_name" ]; then
        log_error "App name and migration name are required for fake migration"
        log_info "Usage: $0 fake <app_name> <migration_name>"
        exit 1
    fi
    
    log_warning "Faking migration: $app_name.$migration_name"
    log_warning "This will mark the migration as applied without actually running it"
    
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py migrate --fake "$app_name" "$migration_name"
        log_success "Migration faked successfully"
    else
        log_info "Operation cancelled"
    fi
}

# Rollback migrations
rollback_migration() {
    local app_name="$1"
    local migration_name="$2"
    
    if [ -z "$app_name" ]; then
        log_error "App name is required for rollback"
        log_info "Usage: $0 rollback <app_name> [migration_name]"
        exit 1
    fi
    
    log_warning "Rolling back migrations for app: $app_name"
    
    if [ -n "$migration_name" ]; then
        log_warning "Rolling back to migration: $migration_name"
    else
        log_warning "Rolling back all migrations for the app"
        migration_name="zero"
    fi
    
    read -p "Are you sure you want to rollback? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_migration_backup
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py migrate "$app_name" "$migration_name"
        log_success "Migration rollback completed"
    else
        log_info "Operation cancelled"
    fi
}

# Merge conflicting migrations
merge_migrations() {
    local app_name="${1:-}"
    
    log_info "Merging conflicting migrations..."
    
    if [ -n "$app_name" ]; then
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py makemigrations --merge "$app_name"
    else
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py makemigrations --merge
    fi
    
    log_success "Migration merge completed"
}

# Reset migrations (DANGEROUS - development only)
reset_migrations() {
    local app_name="$1"
    
    if [ -z "$app_name" ]; then
        log_error "App name is required for reset"
        log_info "Usage: $0 reset <app_name>"
        exit 1
    fi
    
    log_error "WARNING: This will delete all migration files for $app_name!"
    log_error "This operation is IRREVERSIBLE and should only be used in development!"
    
    read -p "Are you absolutely sure? Type 'DELETE' to confirm: " -r
    echo
    
    if [ "$REPLY" = "DELETE" ]; then
        create_migration_backup
        
        # Remove migration files (keep __init__.py)
        docker-compose -f "$COMPOSE_FILE" exec api find "apps/$app_name/migrations/" -name "*.py" -not -name "__init__.py" -delete
        
        # Remove migration records from database
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute('DELETE FROM django_migrations WHERE app = %s', ['$app_name'])
print(f'Deleted {cursor.rowcount} migration records for $app_name')
"
        
        # Create fresh initial migration
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py makemigrations "$app_name"
        
        log_success "Migration reset completed for $app_name"
    else
        log_info "Operation cancelled"
    fi
}

# Validate migrations
validate_migrations() {
    log_info "Validating migrations..."
    
    # Check for unapplied migrations
    local unapplied=$(docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py showmigrations | grep -c "\[ \]" || true)
    
    if [ "$unapplied" -gt 0 ]; then
        log_warning "$unapplied unapplied migrations found"
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py showmigrations | grep "\[ \]"
    else
        log_success "All migrations are applied"
    fi
    
    # Check for migration conflicts
    check_migration_conflicts
    
    # Validate model consistency
    log_info "Checking model consistency..."
    docker-compose -f "$COMPOSE_FILE" exec api python manage.py check
    
    log_success "Migration validation completed"
}

# Squash migrations
squash_migrations() {
    local app_name="$1"
    local start_migration="$2"
    local end_migration="$3"
    
    if [ -z "$app_name" ] || [ -z "$start_migration" ] || [ -z "$end_migration" ]; then
        log_error "App name, start migration, and end migration are required"
        log_info "Usage: $0 squash <app_name> <start_migration> <end_migration>"
        exit 1
    fi
    
    log_info "Squashing migrations for $app_name from $start_migration to $end_migration"
    
    docker-compose -f "$COMPOSE_FILE" exec api python manage.py squashmigrations "$app_name" "$start_migration" "$end_migration"
    
    log_success "Migration squashing completed"
}

# Show migration history
show_migration_history() {
    local app_name="${1:-}"
    
    log_info "Migration history:"
    echo
    
    if [ -n "$app_name" ]; then
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py showmigrations "$app_name" --plan
    else
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py showmigrations --plan
    fi
    
    echo
}

# Generate SQL for migrations
show_migration_sql() {
    local app_name="${1:-}"
    local migration_name="${2:-}"
    
    log_info "Generating SQL for migrations..."
    
    if [ -n "$app_name" ] && [ -n "$migration_name" ]; then
        docker-compose -f "$COMPOSE_FILE" exec api python manage.py sqlmigrate "$app_name" "$migration_name"
    else
        log_error "App name and migration name are required"
        log_info "Usage: $0 sql <app_name> <migration_name>"
        exit 1
    fi
}

# List available backups
list_backups() {
    log_info "Available migration backups:"
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -la "$BACKUP_DIR"/migration_backup_*.sql 2>/dev/null || log_info "No backups found"
    else
        log_info "No backup directory found"
    fi
}

# Restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        log_error "Backup file is required"
        log_info "Usage: $0 restore <backup_file>"
        list_backups
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log_warning "This will restore the database from backup: $backup_file"
    log_warning "All current data will be lost!"
    
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Stop API service
        docker-compose -f "$COMPOSE_FILE" stop api celery-worker
        
        # Restore database
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -c "DROP DATABASE IF EXISTS soundpesa;"
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa -c "CREATE DATABASE soundpesa;"
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U soundpesa soundpesa < "$backup_file"
        
        # Restart services
        docker-compose -f "$COMPOSE_FILE" start api celery-worker
        
        log_success "Database restored from backup"
    else
        log_info "Operation cancelled"
    fi
}

# Show help
show_help() {
    echo "Sound Pesa Database Migration Script"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  status                          - Show migration status"
    echo "  make [app_name]                 - Create new migrations"
    echo "  migrate [app_name] [migration]  - Run migrations"
    echo "  fake <app_name> <migration>     - Mark migration as applied without running"
    echo "  rollback <app_name> [migration] - Rollback migrations"
    echo "  merge [app_name]                - Merge conflicting migrations"
    echo "  reset <app_name>                - Reset all migrations for an app (DANGEROUS)"
    echo "  validate                        - Validate migrations and models"
    echo "  squash <app> <start> <end>      - Squash migrations"
    echo "  history [app_name]              - Show migration history"
    echo "  sql <app_name> <migration>      - Show SQL for a migration"
    echo "  backup                          - Create migration backup"
    echo "  list-backups                    - List available backups"
    echo "  restore <backup_file>           - Restore from backup"
    echo "  help                            - Show this help"
    echo
    echo "Environment Variables:"
    echo "  COMPOSE_FILE                    - Docker Compose file to use (default: docker-compose.dev.yml)"
    echo
    echo "Examples:"
    echo "  $0 status                       - Show current migration status"
    echo "  $0 make authentication          - Create migrations for authentication app"
    echo "  $0 migrate                      - Run all pending migrations"
    echo "  $0 rollback authentication 0001 - Rollback to specific migration"
    echo "  $0 backup                       - Create a backup before migrations"
}

# Main function
main() {
    local command="${1:-status}"
    
    case "$command" in
        "status")
            check_api_service
            show_migration_status
            ;;
        "make")
            check_api_service
            make_migrations "$2"
            ;;
        "migrate")
            check_api_service
            create_migration_backup
            run_migrations "$2" "$3"
            ;;
        "fake")
            check_api_service
            fake_migration "$2" "$3"
            ;;
        "rollback")
            check_api_service
            rollback_migration "$2" "$3"
            ;;
        "merge")
            check_api_service
            merge_migrations "$2"
            ;;
        "reset")
            check_api_service
            reset_migrations "$2"
            ;;
        "validate")
            check_api_service
            validate_migrations
            ;;
        "squash")
            check_api_service
            squash_migrations "$2" "$3" "$4"
            ;;
        "history")
            check_api_service
            show_migration_history "$2"
            ;;
        "sql")
            check_api_service
            show_migration_sql "$2" "$3"
            ;;
        "backup")
            check_api_service
            create_migration_backup
            ;;
        "list-backups")
            list_backups
            ;;
        "restore")
            check_api_service
            restore_backup "$2"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"