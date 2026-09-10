"""
Custom middleware for Sound Pesa platform.
"""
import json
import time
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from sound_pesa.metrics import track_security_event

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to add structured logging with correlation IDs and request context.
    """
    
    def process_request(self, request):
        """Add correlation ID and start time to request."""
        request.correlation_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Log incoming request
        self._log_request(request)
        
        return None
    
    def process_response(self, request, response):
        """Log response details."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            self._log_response(request, response, duration)
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions with context."""
        self._log_exception(request, exception)
        return None
    
    def _log_request(self, request):
        """Log structured request information."""
        log_data = {
            'event_type': 'http_request',
            'correlation_id': getattr(request, 'correlation_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'user_id': str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'content_length': request.META.get('CONTENT_LENGTH', 0)
        }
        
        logger.info(json.dumps(log_data))
    
    def _log_response(self, request, response, duration):
        """Log structured response information."""
        log_data = {
            'event_type': 'http_response',
            'correlation_id': getattr(request, 'correlation_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'response_size': len(response.content) if hasattr(response, 'content') else 0,
            'user_id': str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request)
        }
        
        # Log level based on status code
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
    
    def _log_exception(self, request, exception):
        """Log structured exception information."""
        log_data = {
            'event_type': 'http_exception',
            'correlation_id': getattr(request, 'correlation_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'user_id': str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request)
        }
        
        logger.error(json.dumps(log_data), exc_info=True)
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Middleware to track security-related events and suspicious activities.
    """
    
    def process_request(self, request):
        """Monitor for suspicious request patterns."""
        # Track potential security events
        self._check_suspicious_patterns(request)
        return None
    
    def process_response(self, request, response):
        """Monitor response patterns for security events."""
        # Track failed authentication attempts
        if (request.path.startswith('/api/auth/') and 
            response.status_code in [401, 403]):
            self._log_security_event(
                'failed_authentication',
                request,
                {'status_code': response.status_code}
            )
            
            # Update Prometheus metrics
            track_security_event(
                'failed_login',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        return response
    
    def _check_suspicious_patterns(self, request):
        """Check for suspicious request patterns."""
        suspicious_indicators = []
        
        # Check for SQL injection patterns
        query_string = request.META.get('QUERY_STRING', '')
        if any(pattern in query_string.lower() for pattern in 
               ['union select', 'drop table', 'insert into', '--', ';']):
            suspicious_indicators.append('sql_injection_attempt')
        
        # Check for XSS patterns
        if any(pattern in query_string.lower() for pattern in 
               ['<script', 'javascript:', 'onerror=', 'onload=']):
            suspicious_indicators.append('xss_attempt')
        
        # Check for path traversal
        if '../' in request.path or '..\\' in request.path:
            suspicious_indicators.append('path_traversal_attempt')
        
        # Check for excessive request rate (basic check)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or len(user_agent) < 10:
            suspicious_indicators.append('suspicious_user_agent')
        
        # Log suspicious activities
        if suspicious_indicators:
            self._log_security_event(
                'suspicious_request',
                request,
                {'indicators': suspicious_indicators}
            )
    
    def _log_security_event(self, event_type, request, additional_data=None):
        """Log security events with structured format."""
        log_data = {
            'event_type': 'security_event',
            'security_event_type': event_type,
            'correlation_id': getattr(request, 'correlation_id', 'unknown'),
            'timestamp': time.time(),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'user_id': str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
        }
        
        if additional_data:
            log_data.update(additional_data)
        
        logger.warning(json.dumps(log_data))
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TransactionAuditMiddleware(MiddlewareMixin):
    """
    Middleware to audit transaction-related activities.
    """
    
    def process_request(self, request):
        """Track transaction-related requests."""
        if request.path.startswith('/api/transactions/'):
            self._log_transaction_audit(request, 'transaction_request')
        return None
    
    def process_response(self, request, response):
        """Audit transaction responses."""
        if request.path.startswith('/api/transactions/'):
            self._log_transaction_audit(
                request, 
                'transaction_response',
                {'status_code': response.status_code}
            )
        return response
    
    def _log_transaction_audit(self, request, event_type, additional_data=None):
        """Log transaction audit events."""
        log_data = {
            'event_type': 'transaction_audit',
            'audit_event_type': event_type,
            'correlation_id': getattr(request, 'correlation_id', 'unknown'),
            'timestamp': time.time(),
            'user_id': str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
        
        if additional_data:
            log_data.update(additional_data)
        
        logger.info(json.dumps(log_data))
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip