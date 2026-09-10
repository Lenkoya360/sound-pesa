#!/bin/bash

# Sound Pesa Platform - Database Seeding Script
# This script seeds the database with initial data for development and testing

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

# Create superuser
create_superuser() {
    log_info "Creating Django superuser..."
    
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser(
        username='admin',
        email='admin@soundpesa.com',
        password='admin123'
    )
    print('✓ Superuser created: admin / admin123')
else:
    print('ℹ Superuser already exists')
"
    
    log_success "Superuser setup completed"
}

# Create test users
create_test_users() {
    log_info "Creating test users..."
    
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.authentication.models import UserProfile
import uuid

User = get_user_model()

# Test users data
test_users = [
    {
        'username': 'alice',
        'email': 'alice@example.com',
        'password': 'testpass123',
        'first_name': 'Alice',
        'last_name': 'Johnson',
        'country': 'US'
    },
    {
        'username': 'bob',
        'email': 'bob@example.com',
        'password': 'testpass123',
        'first_name': 'Bob',
        'last_name': 'Smith',
        'country': 'CA'
    },
    {
        'username': 'charlie',
        'email': 'charlie@example.com',
        'password': 'testpass123',
        'first_name': 'Charlie',
        'last_name': 'Brown',
        'country': 'GB'
    },
    {
        'username': 'diana',
        'email': 'diana@example.com',
        'password': 'testpass123',
        'first_name': 'Diana',
        'last_name': 'Wilson',
        'country': 'AU'
    },
    {
        'username': 'eve',
        'email': 'eve@example.com',
        'password': 'testpass123',
        'first_name': 'Eve',
        'last_name': 'Davis',
        'country': 'DE'
    }
]

created_count = 0
for user_data in test_users:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        email=user_data['email'],
        defaults={
            'is_active': True,
            'two_factor_enabled': False,
            'kyc_status': 'approved'
        }
    )
    
    if created:
        user.set_password(user_data['password'])
        user.save()
        
        # Create user profile
        UserProfile.objects.create(
            user=user,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            country=user_data['country']
        )
        
        created_count += 1
        print(f'✓ Created user: {user.username} ({user.email})')
    else:
        print(f'ℹ User already exists: {user.username}')

print(f'Created {created_count} new test users')
"
    
    log_success "Test users created"
}

# Create test wallets
create_test_wallets() {
    log_info "Creating test wallets..."
    
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, WalletBalance
from decimal import Decimal
import uuid

User = get_user_model()

# Blockchain configurations
blockchains = {
    'bitcoin': {
        'symbol': 'BTC',
        'address_prefix': '1',
        'test_balance': '0.5'
    },
    'ethereum': {
        'symbol': 'ETH',
        'address_prefix': '0x',
        'test_balance': '2.5'
    },
    'cardano': {
        'symbol': 'ADA',
        'address_prefix': 'addr1',
        'test_balance': '1000.0'
    },
    'polkadot': {
        'symbol': 'DOT',
        'address_prefix': '1',
        'test_balance': '50.0'
    }
}

# Get test users (excluding admin)
test_users = User.objects.exclude(username='admin')

created_wallets = 0
for user in test_users:
    for blockchain, config in blockchains.items():
        # Generate test address
        if blockchain == 'bitcoin':
            address = f'1{user.id}TestBitcoinAddress{uuid.uuid4().hex[:20]}'
        elif blockchain == 'ethereum':
            address = f'0x{user.id}{uuid.uuid4().hex[:38]}'
        elif blockchain == 'cardano':
            address = f'addr1{user.id}test{uuid.uuid4().hex[:90]}'
        else:  # polkadot
            address = f'1{user.id}TestPolkadotAddress{uuid.uuid4().hex[:35]}'
        
        # Create wallet
        wallet, created = Wallet.objects.get_or_create(
            user=user,
            blockchain=blockchain,
            defaults={
                'address': address,
                'encrypted_private_key': f'encrypted_key_{blockchain}_{user.id}',
                'label': f'{user.first_name}\'s {config[\"symbol\"]} Wallet',
                'is_active': True
            }
        )
        
        if created:
            # Create wallet balance
            WalletBalance.objects.create(
                wallet=wallet,
                balance=Decimal(config['test_balance']),
                confirmed_balance=Decimal(config['test_balance']),
                unconfirmed_balance=Decimal('0')
            )
            
            created_wallets += 1
            print(f'✓ Created {blockchain} wallet for {user.username}: {address[:20]}...')
        else:
            print(f'ℹ {blockchain} wallet already exists for {user.username}')

print(f'Created {created_wallets} new wallets')
"
    
    log_success "Test wallets created"
}

# Create test transactions
create_test_transactions() {
    log_info "Creating test transactions..."
    
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet
from apps.transactions.models import Transaction
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
import random

User = get_user_model()

# Get test users and their wallets
test_users = list(User.objects.exclude(username='admin'))
wallets = list(Wallet.objects.filter(user__in=test_users))

if len(wallets) < 2:
    print('Not enough wallets to create test transactions')
    exit()

# Transaction statuses and their probabilities
statuses = [
    ('confirmed', 0.7),
    ('pending', 0.2),
    ('failed', 0.08),
    ('cancelled', 0.02)
]

created_transactions = 0
for i in range(20):  # Create 20 test transactions
    # Select random wallets
    from_wallet = random.choice(wallets)
    to_wallet = random.choice([w for w in wallets if w != from_wallet and w.blockchain == from_wallet.blockchain])
    
    # Generate random amount
    if from_wallet.blockchain == 'bitcoin':
        amount = Decimal(str(round(random.uniform(0.001, 0.1), 8)))
        fee = Decimal(str(round(random.uniform(0.0001, 0.001), 8)))
    elif from_wallet.blockchain == 'ethereum':
        amount = Decimal(str(round(random.uniform(0.01, 1.0), 6)))
        fee = Decimal(str(round(random.uniform(0.001, 0.01), 6)))
    elif from_wallet.blockchain == 'cardano':
        amount = Decimal(str(round(random.uniform(1, 100), 2)))
        fee = Decimal(str(round(random.uniform(0.1, 2), 2)))
    else:  # polkadot
        amount = Decimal(str(round(random.uniform(0.1, 10), 4)))
        fee = Decimal(str(round(random.uniform(0.01, 0.1), 4)))
    
    # Select random status
    rand = random.random()
    cumulative = 0
    selected_status = 'pending'
    for status, probability in statuses:
        cumulative += probability
        if rand <= cumulative:
            selected_status = status
            break
    
    # Generate transaction hash for confirmed transactions
    tx_hash = None
    block_height = None
    confirmations = 0
    confirmed_at = None
    
    if selected_status == 'confirmed':
        tx_hash = f'{from_wallet.blockchain}_{uuid.uuid4().hex}'
        block_height = random.randint(1000000, 2000000)
        confirmations = random.randint(6, 100)
        confirmed_at = datetime.now() - timedelta(hours=random.randint(1, 168))
    
    # Create transaction
    transaction = Transaction.objects.create(
        user=from_wallet.user,
        from_wallet=from_wallet,
        to_address=to_wallet.address,
        blockchain=from_wallet.blockchain,
        amount=amount,
        fee=fee,
        status=selected_status,
        transaction_hash=tx_hash,
        block_height=block_height,
        confirmations=confirmations,
        confirmed_at=confirmed_at,
        notes=f'Test transaction #{i+1}'
    )
    
    created_transactions += 1
    print(f'✓ Created {selected_status} transaction: {amount} {from_wallet.blockchain.upper()} from {from_wallet.user.username} to {to_wallet.user.username}')

print(f'Created {created_transactions} test transactions')
"
    
    log_success "Test transactions created"
}

# Create blockchain status data
create_blockchain_status() {
    log_info "Creating blockchain status data..."
    
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py shell -c "
from apps.blockchain.models import BlockchainStatus
from datetime import datetime
import random

# Blockchain status data
blockchain_data = {
    'bitcoin': {
        'current_block': 800000,
        'highest_block': 800000,
        'peer_count': 8
    },
    'ethereum': {
        'current_block': 18000000,
        'highest_block': 18000000,
        'peer_count': 12
    },
    'cardano': {
        'current_block': 9000000,
        'highest_block': 9000000,
        'peer_count': 6
    },
    'polkadot': {
        'current_block': 16000000,
        'highest_block': 16000000,
        'peer_count': 10
    }
}

created_count = 0
for blockchain, data in blockchain_data.items():
    status, created = BlockchainStatus.objects.get_or_create(
        blockchain=blockchain,
        defaults={
            'is_synced': True,
            'current_block': data['current_block'],
            'highest_block': data['highest_block'],
            'sync_percentage': 100.0,
            'peer_count': data['peer_count'],
            'last_block_time': datetime.now(),
            'network': 'testnet'
        }
    )
    
    if created:
        created_count += 1
        print(f'✓ Created blockchain status for {blockchain}')
    else:
        print(f'ℹ Blockchain status already exists for {blockchain}')

print(f'Created {created_count} blockchain status records')
"
    
    log_success "Blockchain status data created"
}

# Seed development data
seed_development() {
    log_info "Seeding development data..."
    
    create_superuser
    create_test_users
    create_test_wallets
    create_test_transactions
    create_blockchain_status
    
    log_success "Development data seeding completed"
}

# Seed production data (minimal)
seed_production() {
    log_info "Seeding production data..."
    
    create_superuser
    create_blockchain_status
    
    log_success "Production data seeding completed"
}

# Clear all data
clear_data() {
    log_warning "This will delete ALL data from the database!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Clearing database data..."
        
        docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, WalletBalance
from apps.transactions.models import Transaction
from apps.blockchain.models import BlockchainStatus

User = get_user_model()

# Delete in correct order to avoid foreign key constraints
Transaction.objects.all().delete()
WalletBalance.objects.all().delete()
Wallet.objects.all().delete()
BlockchainStatus.objects.all().delete()
User.objects.exclude(username='admin').delete()

print('✓ All data cleared (except admin user)')
"
        
        log_success "Database data cleared"
    else
        log_info "Operation cancelled"
    fi
}

# Show database statistics
show_stats() {
    log_info "Database statistics:"
    
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, WalletBalance
from apps.transactions.models import Transaction
from apps.blockchain.models import BlockchainStatus

User = get_user_model()

print(f'Users: {User.objects.count()}')
print(f'Wallets: {Wallet.objects.count()}')
print(f'Wallet Balances: {WalletBalance.objects.count()}')
print(f'Transactions: {Transaction.objects.count()}')
print(f'Blockchain Status Records: {BlockchainStatus.objects.count()}')

print('\nTransaction Status Breakdown:')
for status in ['pending', 'confirmed', 'failed', 'cancelled']:
    count = Transaction.objects.filter(status=status).count()
    print(f'  {status.capitalize()}: {count}')

print('\nWallets by Blockchain:')
for blockchain in ['bitcoin', 'ethereum', 'cardano', 'polkadot']:
    count = Wallet.objects.filter(blockchain=blockchain).count()
    print(f'  {blockchain.capitalize()}: {count}')
"
}

# Export data
export_data() {
    local export_file="database_export_$(date +%Y%m%d_%H%M%S).json"
    
    log_info "Exporting data to $export_file..."
    
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py dumpdata \
        --natural-foreign --natural-primary \
        --exclude=contenttypes --exclude=auth.permission \
        --exclude=sessions --exclude=admin.logentry \
        > "$export_file"
    
    log_success "Data exported to $export_file"
}

# Import data
import_data() {
    local import_file="$1"
    
    if [ -z "$import_file" ]; then
        log_error "Import file is required"
        log_info "Usage: $0 import <file.json>"
        exit 1
    fi
    
    if [ ! -f "$import_file" ]; then
        log_error "Import file not found: $import_file"
        exit 1
    fi
    
    log_info "Importing data from $import_file..."
    
    docker-compose -f "$COMPOSE_FILE" exec -T api python manage.py loaddata < "$import_file"
    
    log_success "Data imported from $import_file"
}

# Show help
show_help() {
    echo "Sound Pesa Database Seeding Script"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  development     - Seed development data (users, wallets, transactions)"
    echo "  production      - Seed minimal production data (superuser, blockchain status)"
    echo "  superuser       - Create Django superuser only"
    echo "  users           - Create test users only"
    echo "  wallets         - Create test wallets only"
    echo "  transactions    - Create test transactions only"
    echo "  blockchain      - Create blockchain status data only"
    echo "  clear           - Clear all data (DANGEROUS)"
    echo "  stats           - Show database statistics"
    echo "  export          - Export data to JSON file"
    echo "  import <file>   - Import data from JSON file"
    echo "  help            - Show this help"
    echo
    echo "Environment Variables:"
    echo "  COMPOSE_FILE    - Docker Compose file to use (default: docker-compose.dev.yml)"
    echo
    echo "Examples:"
    echo "  $0 development  - Seed full development environment"
    echo "  $0 production   - Seed production environment"
    echo "  $0 users        - Create test users only"
    echo "  $0 clear        - Clear all data"
    echo "  $0 stats        - Show current database statistics"
}

# Main function
main() {
    local command="${1:-development}"
    
    case "$command" in
        "development"|"dev")
            check_api_service
            seed_development
            show_stats
            ;;
        "production"|"prod")
            check_api_service
            seed_production
            ;;
        "superuser")
            check_api_service
            create_superuser
            ;;
        "users")
            check_api_service
            create_test_users
            ;;
        "wallets")
            check_api_service
            create_test_wallets
            ;;
        "transactions")
            check_api_service
            create_test_transactions
            ;;
        "blockchain")
            check_api_service
            create_blockchain_status
            ;;
        "clear")
            check_api_service
            clear_data
            ;;
        "stats")
            check_api_service
            show_stats
            ;;
        "export")
            check_api_service
            export_data
            ;;
        "import")
            check_api_service
            import_data "$2"
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