"""
Wallet management views.
"""
import logging
from django.db.models import Count, Q
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from .models import Wallet, WalletBalance, WalletTransaction
from .serializers import (
    WalletSerializer,
    WalletTransactionSerializer,
    WalletCreationSerializer,
    WalletSummarySerializer
)
from .services import WalletService

logger = logging.getLogger(__name__)


class WalletListView(ListAPIView):
    """
    List all wallets for the authenticated user.
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return wallets for the current user.
        """
        return Wallet.objects.filter(
            user=self.request.user
        ).select_related('balance').order_by('blockchain')


class WalletCreateView(APIView):
    """
    Create a new wallet for a specific blockchain.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Create a new wallet for the specified blockchain.
        """
        serializer = WalletCreationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            blockchain = serializer.validated_data['blockchain']
            
            try:
                wallet = WalletService.create_wallet(request.user, blockchain)
                wallet_serializer = WalletSerializer(wallet)
                
                return Response({
                    'message': f'{blockchain.title()} wallet created successfully',
                    'wallet': wallet_serializer.data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Wallet creation failed for user {request.user.email}: {str(e)}")
                return Response({
                    'error': 'Wallet creation failed',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': 'Invalid wallet creation request',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class WalletCreateAllView(APIView):
    """
    Create wallets for all supported blockchains.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Create wallets for all supported blockchains.
        """
        try:
            wallets = WalletService.create_all_wallets(request.user)
            wallet_serializers = {
                blockchain: WalletSerializer(wallet).data 
                for blockchain, wallet in wallets.items()
            }
            
            return Response({
                'message': 'Wallets created successfully',
                'wallets': wallet_serializers
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Bulk wallet creation failed for user {request.user.email}: {str(e)}")
            return Response({
                'error': 'Wallet creation failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletDetailView(RetrieveAPIView):
    """
    Get details for a specific wallet.
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return wallets for the current user.
        """
        return Wallet.objects.filter(
            user=self.request.user
        ).select_related('balance')


class WalletBalanceView(APIView):
    """
    Get balance for a specific wallet or blockchain.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, blockchain):
        """
        Get balance for the specified blockchain wallet.
        """
        try:
            wallet = Wallet.objects.select_related('balance').get(
                user=request.user,
                blockchain=blockchain
            )
            
            balance = WalletService.get_wallet_balance(wallet)
            
            if balance:
                return Response({
                    'blockchain': blockchain,
                    'address': wallet.address,
                    'balance': str(balance.balance),
                    'confirmed_balance': str(balance.confirmed_balance),
                    'unconfirmed_balance': str(balance.unconfirmed_balance),
                    'last_updated': balance.last_updated
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Balance information not available'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Wallet.DoesNotExist:
            return Response({
                'error': f'No {blockchain} wallet found for user'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Balance retrieval failed: {str(e)}")
            return Response({
                'error': 'Failed to retrieve balance',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletTransactionPagination(PageNumberPagination):
    """
    Custom pagination for wallet transactions.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class WalletTransactionHistoryView(ListAPIView):
    """
    Get transaction history for a specific wallet.
    """
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = WalletTransactionPagination
    
    def get_queryset(self):
        """
        Return transactions for the specified wallet.
        """
        blockchain = self.kwargs.get('blockchain')
        
        try:
            wallet = Wallet.objects.get(
                user=self.request.user,
                blockchain=blockchain
            )
            
            return WalletTransaction.objects.filter(
                wallet=wallet
            ).order_by('-created_at')
            
        except Wallet.DoesNotExist:
            return WalletTransaction.objects.none()


class WalletSummaryView(APIView):
    """
    Get summary information for all user wallets.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get wallet summary for the authenticated user.
        """
        try:
            user_wallets = Wallet.objects.filter(user=request.user)
            
            # Get wallet statistics
            total_wallets = user_wallets.count()
            active_wallets = user_wallets.filter(is_active=True).count()
            blockchains = list(user_wallets.values_list('blockchain', flat=True))
            
            # Get latest transaction
            latest_transaction = WalletTransaction.objects.filter(
                wallet__user=request.user
            ).order_by('-created_at').first()
            
            summary_data = {
                'total_wallets': total_wallets,
                'active_wallets': active_wallets,
                'blockchains': blockchains,
                'total_balance_usd': 0.00,  # Placeholder - implement price conversion
                'last_transaction': latest_transaction.created_at if latest_transaction else None
            }
            
            serializer = WalletSummarySerializer(summary_data)
            
            return Response({
                'summary': serializer.data,
                'wallets': WalletSerializer(user_wallets, many=True).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Wallet summary failed for user {request.user.email}: {str(e)}")
            return Response({
                'error': 'Failed to retrieve wallet summary',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_wallet_balance(request, blockchain):
    """
    Refresh balance for a specific blockchain wallet.
    """
    try:
        wallet = Wallet.objects.get(
            user=request.user,
            blockchain=blockchain
        )
        
        # In a real implementation, this would query the blockchain
        # For now, we'll just return the current balance
        balance = WalletService.get_wallet_balance(wallet)
        
        if balance:
            return Response({
                'message': 'Balance refreshed successfully',
                'blockchain': blockchain,
                'balance': str(balance.balance),
                'last_updated': balance.last_updated
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to refresh balance'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Wallet.DoesNotExist:
        return Response({
            'error': f'No {blockchain} wallet found for user'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Balance refresh failed: {str(e)}")
        return Response({
            'error': 'Failed to refresh balance',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)