"""
Custom logging formatters for structured logging.
"""
import json
import logging
import traceback
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        # Add transaction ID if available
        if hasattr(record, 'transaction_id'):
            log_entry['transaction_id'] = record.transaction_id
        
        # Add blockchain if available
        if hasattr(record, 'blockchain'):
            log_entry['blockchain'] = record.blockchain
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info', 'correlation_id', 'user_id', 
                          'transaction_id', 'blockchain']:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str)


class TransactionLogFormatter(JSONFormatter):
    """
    Specialized formatter for transaction-related logs.
    """
    
    def format(self, record):
        """Format transaction log record with additional context."""
        log_entry = json.loads(super().format(record))
        
        # Add transaction-specific fields
        log_entry['service'] = 'transaction-engine'
        log_entry['category'] = 'transaction'
        
        # Add blockchain-specific context if available
        if hasattr(record, 'blockchain'):
            log_entry['blockchain'] = record.blockchain
        
        if hasattr(record, 'transaction_hash'):
            log_entry['transaction_hash'] = record.transaction_hash
        
        if hasattr(record, 'wallet_address'):
            log_entry['wallet_address'] = record.wallet_address
        
        if hasattr(record, 'amount'):
            log_entry['amount'] = record.amount
        
        return json.dumps(log_entry, default=str)


class SecurityLogFormatter(JSONFormatter):
    """
    Specialized formatter for security-related logs.
    """
    
    def format(self, record):
        """Format security log record with additional context."""
        log_entry = json.loads(super().format(record))
        
        # Add security-specific fields
        log_entry['service'] = 'security-audit'
        log_entry['category'] = 'security'
        
        # Add security context if available
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        
        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type
        
        if hasattr(record, 'risk_level'):
            log_entry['risk_level'] = record.risk_level
        
        return json.dumps(log_entry, default=str)


class BlockchainLogFormatter(JSONFormatter):
    """
    Specialized formatter for blockchain-related logs.
    """
    
    def format(self, record):
        """Format blockchain log record with additional context."""
        log_entry = json.loads(super().format(record))
        
        # Add blockchain-specific fields
        log_entry['service'] = 'blockchain-adapter'
        log_entry['category'] = 'blockchain'
        
        # Add blockchain context if available
        if hasattr(record, 'blockchain'):
            log_entry['blockchain'] = record.blockchain
        
        if hasattr(record, 'block_height'):
            log_entry['block_height'] = record.block_height
        
        if hasattr(record, 'peer_count'):
            log_entry['peer_count'] = record.peer_count
        
        if hasattr(record, 'sync_status'):
            log_entry['sync_status'] = record.sync_status
        
        return json.dumps(log_entry, default=str)