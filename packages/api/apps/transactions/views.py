"""
Transaction API views for Sound Pesa platform.
"""
import logging
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from sound_pesa.asyncs import run_async
from .models import Transaction, TransactionEstimate, NetworkFeeRate
from .serializers import (
    TransactionEstimateRequestSerializer, TransactionEstimateSerializer,
    TransactionCreateSerializer, TransactionSerializer,
    TransactionDetailSerializer, TransactionListSerializer,
    TransactionStatusUpdateSerializer
)
from .services import (
    TransactionEstimationService, TransactionCreationService,
    TransactionProcessingService, TransactionMonitoringService
)
from sound_pesa.exceptions import ValidationError, BlockchainError

logger = logging.getLogger(__name__)


class TransactionPagination(PageNumberPagination):
    """Custom pagination for transaction lists."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def estimate_transaction_fee(request):
    """
    Estimate transaction fee for a given transaction.
    
    POST /api/transactions/estimate-fee/
    """
    serializer = TransactionEstimateRequestSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Validation failed', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        estimate = run_async(TransactionEstimationService.estimate_transaction_fee(
            user=request.user,
            from_wallet_id=str(serializer.validated_data['from_wallet_id']),
            to_address=serializer.validated_data['to_address'],
            amount=serializer.validated_data['amount'],
            fee_priority=serializer.validated_data['fee_priority']
        ))
        
        response_serializer = TransactionEstimateSerializer(estimate)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response(
            {'error': 'Validation error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except BlockchainError as e:
        return Response(
            {'error': 'Blockchain error', 'message': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.error(f"Fee estimation error: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'message': 'Failed to estimate fee'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_transaction(request):
    """
    Create a new transaction.
    
    POST /api/transactions/send/
    """
    serializer = TransactionCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Validation failed', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        transaction = run_async(TransactionCreationService.create_transaction(
            user=request.user,
            from_wallet_id=str(serializer.validated_data['from_wallet_id']),
            to_address=serializer.validated_data['to_address'],
            amount=serializer.validated_data['amount'],
            fee_priority=serializer.validated_data['fee_priority'],
            estimate_id=str(serializer.validated_data.get('estimate_id')) if serializer.validated_data.get('estimate_id') else None
        ))
        
        # Queue transaction for asynchronous processing
        from .tasks import process_transaction_task
        process_transaction_task.delay(str(transaction.id))
        
        response_serializer = TransactionSerializer(transaction)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response(
            {'error': 'Validation error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except BlockchainError as e:
        return Response(
            {'error': 'Blockchain error', 'message': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.error(f"Transaction creation error: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'message': 'Failed to create transaction'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TransactionListView(generics.ListAPIView):
    """
    List user's transactions with filtering and pagination.
    
    GET /api/transactions/
    """
    serializer_class = TransactionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TransactionPagination
    
    def get_queryset(self):
        """Filter transactions for the authenticated user."""
        queryset = Transaction.objects.filter(user=self.request.user)
        
        # Filter by blockchain
        blockchain = self.request.query_params.get('blockchain')
        if blockchain:
            queryset = queryset.filter(blockchain=blockchain)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Search by transaction hash or address
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_hash__icontains=search) |
                Q(to_address__icontains=search)
            )
        
        return queryset.select_related('from_wallet').order_by('-created_at')


class TransactionDetailView(generics.RetrieveAPIView):
    """
    Get detailed transaction information.
    
    GET /api/transactions/{id}/
    """
    serializer_class = TransactionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions for the authenticated user."""
        return Transaction.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_transaction_status(request, transaction_id):
    """
    Get current transaction status with real-time blockchain data.
    
    GET /api/transactions/{id}/status/
    """
    try:
        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
            user=request.user
        )
        
        # Update status from blockchain if transaction has hash
        if transaction.transaction_hash:
            run_async(TransactionMonitoringService.update_transaction_status(transaction_id))
            transaction.refresh_from_db()
        
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Transaction status error: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'message': 'Failed to get transaction status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_transaction(request, transaction_id):
    """
    Cancel a pending transaction.
    
    POST /api/transactions/{id}/cancel/
    """
    try:
        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
            user=request.user
        )
        
        if transaction.status != 'pending':
            return Response(
                {'error': 'Transaction cannot be cancelled', 'message': 'Only pending transactions can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if transaction.transaction_hash:
            return Response(
                {'error': 'Transaction cannot be cancelled', 'message': 'Transaction has already been broadcasted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cancel the transaction
        transaction.status = 'cancelled'
        transaction.save()
        
        # Create audit log
        from .models import TransactionAuditLog
        TransactionAuditLog.objects.create(
            transaction=transaction,
            correlation_id=transaction.correlation_id,
            action='cancelled',
            user=request.user,
            message='Transaction cancelled by user'
        )
        
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Transaction cancellation error: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'message': 'Failed to cancel transaction'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_pending_transactions(request):
    """
    Get user's pending transactions.
    
    GET /api/transactions/pending/
    """
    try:
        pending_transactions = Transaction.objects.filter(
            user=request.user,
            status='pending'
        ).select_related('from_wallet').order_by('-created_at')
        
        serializer = TransactionListSerializer(pending_transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Pending transactions error: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'message': 'Failed to get pending transactions'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_transaction_history(request, wallet_id):
    """
    Get transaction history for a specific wallet.
    
    GET /api/wallets/{wallet_id}/transactions/
    """
    try:
        from apps.wallets.models import Wallet
        
        # Verify wallet ownership
        wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user)
        
        transactions = Transaction.objects.filter(
            from_wallet=wallet
        ).order_by('-created_at')
        
        # Apply pagination
        paginator = TransactionPagination()
        page = paginator.paginate_queryset(transactions, request)
        
        if page is not None:
            serializer = TransactionListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = TransactionListSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Transaction history error: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'message': 'Failed to get transaction history'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_transaction_statistics(request):
    """
    Get transaction statistics for the user.
    
    GET /api/transactions/statistics/
    """
    try:
        from django.db.models import Count, Sum
        
        # Get statistics for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        stats = Transaction.objects.filter(
            user=request.user,
            created_at__gte=thirty_days_ago
        ).aggregate(
            total_transactions=Count('id'),
            total_amount=Sum('amount'),
            confirmed_transactions=Count('id', filter=Q(status='confirmed')),
            pending_transactions=Count('id', filter=Q(status='pending')),
            failed_transactions=Count('id', filter=Q(status='failed'))
        )
        
        # Get statistics by blockchain
        blockchain_stats = Transaction.objects.filter(
            user=request.user,
            created_at__gte=thirty_days_ago
        ).values('blockchain').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        response_data = {
            'period': '30_days',
            'summary': stats,
            'by_blockchain': list(blockchain_stats)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Transaction statistics error: {str(e)}")
        return Response(
            {'error': 'Internal server error', 'message': 'Failed to get transaction statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def transaction_system_health(request):
    """
    Get transaction system health status.
    
    GET /api/transactions/health/
    """
    try:
        from django.db.models import Count
        from .tasks import monitor_blockchain_nodes
        
        # Get system statistics
        total_transactions = Transaction.objects.count()
        pending_transactions = Transaction.objects.filter(status='pending').count()
        failed_transactions = Transaction.objects.filter(status='failed').count()
        
        # Get recent transaction activity (last hour)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_transactions = Transaction.objects.filter(
            created_at__gte=one_hour_ago
        ).count()
        
        # Get network fee rates status
        fee_rates_count = NetworkFeeRate.objects.count()
        expected_blockchains = 4  # bitcoin, ethereum, cardano, polkadot
        
        # Check Celery task status (simplified)
        celery_healthy = True  # Would check actual Celery status
        
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'statistics': {
                'total_transactions': total_transactions,
                'pending_transactions': pending_transactions,
                'failed_transactions': failed_transactions,
                'recent_transactions_1h': recent_transactions
            },
            'services': {
                'database': 'healthy',
                'celery': 'healthy' if celery_healthy else 'unhealthy',
                'fee_rates': 'healthy' if fee_rates_count >= expected_blockchains else 'partial'
            },
            'network_fee_rates': {
                'configured_blockchains': fee_rates_count,
                'expected_blockchains': expected_blockchains
            }
        }
        
        # Determine overall health
        if pending_transactions > 100 or failed_transactions > 50:
            health_status['status'] = 'degraded'
        
        if not celery_healthy:
            health_status['status'] = 'unhealthy'
        
        return Response(health_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return Response(
            {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )