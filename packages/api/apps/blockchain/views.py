"""
Blockchain status and introspection views.
"""
import logging

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from sound_pesa.asyncs import run_async
from .models import BlockchainNode, BlockchainAddress
from .serializers import (
    BlockchainNodeSerializer,
    BlockchainAddressSerializer,
    EstimateFeeRequestSerializer,
    TransactionStatusRequestSerializer,
)
from .services import BlockchainService

logger = logging.getLogger(__name__)


class BlockchainStatusListView(ListAPIView):
    """
    List the current status of all configured blockchain nodes.
    """
    serializer_class = BlockchainNodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlockchainNode.objects.all().order_by('blockchain')


class BlockchainStatusView(APIView):
    """
    Return live status for a specific blockchain, refreshing node info
    from the adapter when possible.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, blockchain):
        if not BlockchainService._is_supported(blockchain):
            return Response(
                {'detail': f'Unsupported blockchain: {blockchain}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            node_status = BlockchainService.get_blockchain_status_sync(blockchain)
            return Response(node_status)
        except Exception as e:
            logger.error(f"Failed to fetch blockchain status for {blockchain}: {e}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class BlockchainBalanceView(APIView):
    """
    Fetch the balance for a listed user address on a blockchain.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, blockchain, address):
        if not BlockchainService._is_supported(blockchain):
            return Response(
                {'detail': f'Unsupported blockchain: {blockchain}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            balance = run_async(
                BlockchainService.get_balance(request.user, blockchain, address)
            )
            return Response({'blockchain': blockchain, 'address': address, 'balance': balance})
        except Exception as e:
            logger.error(f"Balance fetch failed for {blockchain}/{address}: {e}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class BlockchainAddressCreateView(APIView):
    """
    Generate a new address for the authenticated user on a blockchain.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from rest_framework import serializers as drf_serializers

        blockchain = request.data.get('blockchain')
        if not BlockchainService._is_supported(blockchain):
            return Response(
                {'detail': f'Unsupported blockchain: {blockchain}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            address_info = run_async(
                BlockchainService.generate_address(request.user, blockchain)
            )
            address_obj = BlockchainAddress.objects.filter(
                user=request.user,
                blockchain=blockchain,
                address=address_info.get('address'),
            ).first()
            serializer = BlockchainAddressSerializer(address_obj) if address_obj else address_info
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Address generation failed for {blockchain}: {e}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class BlockchainEstimateFeeView(APIView):
    """
    Estimate the transaction fee for a transfer attempt.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = EstimateFeeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            fee = run_async(
                BlockchainService.estimate_transaction_fee(
                    data['blockchain'],
                    data['from_address'],
                    data['to_address'],
                    str(data['amount']),
                )
            )
            return Response({'blockchain': data['blockchain'], 'estimated_fee': fee})
        except Exception as e:
            logger.error(f"Fee estimation failed for {data['blockchain']}: {e}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class BlockchainTransactionStatusView(APIView):
    """
    Fetch the current status of a transaction on a blockchain.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TransactionStatusRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            tx_details = run_async(
                BlockchainService.get_transaction_status(data['tx_hash'], data['blockchain'])
            )
            return Response({'blockchain': data['blockchain'], **tx_details})
        except Exception as e:
            logger.error(f"Transaction status failed for {data['tx_hash']}: {e}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )