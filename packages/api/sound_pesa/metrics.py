"""
Prometheus metrics configuration for Sound Pesa platform.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from django.conf import settings

# API Metrics
api_requests_total = Counter(
    'django_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'django_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Transaction Metrics
transaction_processing_time = Histogram(
    'sound_pesa_transaction_processing_seconds',
    'Transaction processing time in seconds',
    ['blockchain', 'transaction_type']
)

transaction_success_total = Counter(
    'sound_pesa_transaction_success_total',
    'Total successful transactions',
    ['blockchain', 'transaction_type']
)

transaction_failures_total = Counter(
    'sound_pesa_transaction_failures_total',
    'Total failed transactions',
    ['blockchain', 'transaction_type', 'error_type']
)

transaction_queue_size = Gauge(
    'sound_pesa_transaction_queue_size',
    'Number of transactions in processing queue'
)

# Blockchain Node Metrics
blockchain_sync_lag_blocks = Gauge(
    'sound_pesa_blockchain_sync_lag_blocks',
    'Number of blocks behind the network',
    ['blockchain']
)

blockchain_peer_count = Gauge(
    'sound_pesa_blockchain_peer_count',
    'Number of connected peers',
    ['blockchain']
)

blockchain_last_block_time = Gauge(
    'sound_pesa_blockchain_last_block_timestamp',
    'Timestamp of the last processed block',
    ['blockchain']
)

# Wallet Metrics
wallet_balance_total = Gauge(
    'sound_pesa_wallet_balance_total',
    'Total wallet balance in base units',
    ['blockchain', 'wallet_id']
)

active_wallets_count = Gauge(
    'sound_pesa_active_wallets_count',
    'Number of active wallets',
    ['blockchain']
)

# Security Metrics
failed_login_attempts_total = Counter(
    'sound_pesa_failed_login_attempts_total',
    'Total failed login attempts',
    ['ip_address', 'user_agent']
)

suspicious_transactions_total = Counter(
    'sound_pesa_suspicious_transactions_total',
    'Total suspicious transactions detected',
    ['blockchain', 'reason']
)

# System Info
platform_info = Info(
    'sound_pesa_platform_info',
    'Platform version and configuration information'
)

# Initialize platform info
platform_info.info({
    'version': getattr(settings, 'VERSION', '1.0.0'),
    'environment': getattr(settings, 'ENVIRONMENT', 'development'),
    'supported_blockchains': 'bitcoin,ethereum,cardano,polkadot'
})


def track_api_metrics(view_func):
    """Decorator to track API endpoint metrics."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        
        # Extract endpoint name from view function
        endpoint = f"{view_func.__module__}.{view_func.__name__}"
        method = request.method
        
        try:
            response = view_func(request, *args, **kwargs)
            status = str(response.status_code)
            
            # Track successful request
            api_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            return response
            
        except Exception as e:
            # Track failed request
            api_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status='500'
            ).inc()
            raise
            
        finally:
            # Track request duration
            duration = time.time() - start_time
            api_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    return wrapper


def track_transaction_metrics(blockchain, transaction_type):
    """Decorator to track transaction processing metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Track successful transaction
                transaction_success_total.labels(
                    blockchain=blockchain,
                    transaction_type=transaction_type
                ).inc()
                
                return result
                
            except Exception as e:
                # Track failed transaction
                error_type = type(e).__name__
                transaction_failures_total.labels(
                    blockchain=blockchain,
                    transaction_type=transaction_type,
                    error_type=error_type
                ).inc()
                raise
                
            finally:
                # Track processing time
                duration = time.time() - start_time
                transaction_processing_time.labels(
                    blockchain=blockchain,
                    transaction_type=transaction_type
                ).observe(duration)
        
        return wrapper
    return decorator


def update_blockchain_metrics(blockchain, sync_lag=None, peer_count=None, last_block_time=None):
    """Update blockchain node metrics."""
    if sync_lag is not None:
        blockchain_sync_lag_blocks.labels(blockchain=blockchain).set(sync_lag)
    
    if peer_count is not None:
        blockchain_peer_count.labels(blockchain=blockchain).set(peer_count)
    
    if last_block_time is not None:
        blockchain_last_block_time.labels(blockchain=blockchain).set(last_block_time)


def update_wallet_metrics(blockchain, wallet_id, balance):
    """Update wallet balance metrics."""
    wallet_balance_total.labels(
        blockchain=blockchain,
        wallet_id=wallet_id
    ).set(float(balance))


def track_security_event(event_type, **labels):
    """Track security-related events."""
    if event_type == 'failed_login':
        failed_login_attempts_total.labels(
            ip_address=labels.get('ip_address', 'unknown'),
            user_agent=labels.get('user_agent', 'unknown')
        ).inc()
    
    elif event_type == 'suspicious_transaction':
        suspicious_transactions_total.labels(
            blockchain=labels.get('blockchain', 'unknown'),
            reason=labels.get('reason', 'unknown')
        ).inc()