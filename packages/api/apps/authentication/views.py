"""
Authentication views for Sound Pesa platform.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from sound_pesa.vault_client import get_vault_client
from sound_pesa.metrics import track_security_event
from .models import User
from .serializers import UserRegistrationSerializer, UserSerializer
import logging

logger = logging.getLogger('sound_pesa.security')
User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """User registration view."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Handle user registration with security logging."""
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == 201:
            logger.info({
                'event_type': 'user_registration',
                'user_email': request.data.get('email'),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            })
        
        return response
    
    def _get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserLoginView(TokenObtainPairView):
    """Custom JWT token obtain view with security logging."""
    
    def post(self, request, *args, **kwargs):
        """Handle token creation with security audit."""
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log successful authentication
            logger.info({
                'event_type': 'successful_authentication',
                'user_email': request.data.get('email'),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            })
        else:
            # Log failed authentication
            logger.warning({
                'event_type': 'failed_authentication',
                'user_email': request.data.get('email'),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'status_code': response.status_code
            })
            
            # Track security metrics
            track_security_event(
                'failed_login',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        return response
    
    def _get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([AllowAny])
def vault_health_check(request):
    """
    Health check endpoint for Vault integration.
    """
    try:
        vault_client = get_vault_client()
        health_status = vault_client.health_check()
        
        return JsonResponse({
            'vault_health': health_status,
            'timestamp': logger.info.__self__.name
        })
        
    except Exception as e:
        logger.error({
            'event_type': 'vault_health_check_error',
            'error': str(e)
        })
        
        return JsonResponse({
            'vault_health': {
                'healthy': False,
                'error': str(e)
            }
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rotate_encryption_keys(request):
    """
    Endpoint to rotate Vault encryption keys (admin only).
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin privileges required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        vault_client = get_vault_client()
        
        # Rotate private keys encryption key
        private_key_rotated = vault_client.rotate_encryption_key('private-keys')
        
        # Rotate API keys encryption key
        api_key_rotated = vault_client.rotate_encryption_key('api-keys')
        
        logger.info({
            'event_type': 'encryption_keys_rotated',
            'user_id': str(request.user.id),
            'private_keys_rotated': private_key_rotated,
            'api_keys_rotated': api_key_rotated
        })
        
        return Response({
            'message': 'Encryption keys rotation completed',
            'private_keys_rotated': private_key_rotated,
            'api_keys_rotated': api_key_rotated
        })
        
    except Exception as e:
        logger.error({
            'event_type': 'encryption_key_rotation_error',
            'user_id': str(request.user.id),
            'error': str(e)
        })
        
        return Response(
            {'error': f'Key rotation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class UserLogoutView(APIView):
    """User logout view."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle user logout."""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logger.info({
                'event_type': 'user_logout',
                'user_id': str(request.user.id),
                'ip_address': self._get_client_ip(request)
            })
            
            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Return the current user."""
        return self.request.user


class PasswordChangeView(APIView):
    """Password change view."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle password change."""
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Both old and new passwords are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        if not user.check_password(old_password):
            logger.warning({
                'event_type': 'password_change_failed',
                'user_id': str(user.id),
                'reason': 'incorrect_old_password',
                'ip_address': self._get_client_ip(request)
            })
            return Response(
                {'error': 'Incorrect old password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        logger.info({
            'event_type': 'password_changed',
            'user_id': str(user.id),
            'ip_address': self._get_client_ip(request)
        })
        
        return Response({'message': 'Password changed successfully'})
    
    def _get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_status(request):
    """Get current user status."""
    return Response({
        'user_id': str(request.user.id),
        'email': request.user.email,
        'is_authenticated': True,
        'is_active': request.user.is_active
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def vault_health_check(request):
    """
    Health check endpoint for Vault integration.
    """
    try:
        vault_client = get_vault_client()
        health_status = vault_client.health_check()
        
        return JsonResponse({
            'vault_health': health_status,
            'timestamp': logger.info.__self__.name
        })
        
    except Exception as e:
        logger.error({
            'event_type': 'vault_health_check_error',
            'error': str(e)
        })
        
        return JsonResponse({
            'vault_health': {
                'healthy': False,
                'error': str(e)
            }
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rotate_encryption_keys(request):
    """
    Endpoint to rotate Vault encryption keys (admin only).
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin privileges required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        vault_client = get_vault_client()
        
        # Rotate private keys encryption key
        private_key_rotated = vault_client.rotate_encryption_key('private-keys')
        
        # Rotate API keys encryption key
        api_key_rotated = vault_client.rotate_encryption_key('api-keys')
        
        logger.info({
            'event_type': 'encryption_keys_rotated',
            'user_id': str(request.user.id),
            'private_keys_rotated': private_key_rotated,
            'api_keys_rotated': api_key_rotated
        })
        
        return Response({
            'message': 'Encryption keys rotation completed',
            'private_keys_rotated': private_key_rotated,
            'api_keys_rotated': api_key_rotated
        })
        
    except Exception as e:
        logger.error({
            'event_type': 'encryption_key_rotation_error',
            'user_id': str(request.user.id),
            'error': str(e)
        })
        
        return Response(
            {'error': f'Key rotation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )