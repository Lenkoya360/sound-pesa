"""
Serializers for the blockchain app.
"""
from rest_framework import serializers

from .models import BlockchainNode, BlockchainTransaction, BlockchainAddress, BLOCKCHAIN_CHOICES


class BlockchainNodeSerializer(serializers.ModelSerializer):
    """Serializer for blockchain node status."""

    class Meta:
        model = BlockchainNode
        fields = (
            'id',
            'blockchain',
            'network',
            'is_active',
            'is_synced',
            'current_block_height',
            'peer_count',
            'last_checked',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'last_checked',
        )


class BlockchainAddressSerializer(serializers.ModelSerializer):
    """Serializer for a user's blockchain address."""

    class Meta:
        model = BlockchainAddress
        fields = (
            'id',
            'blockchain',
            'address',
            'is_active',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')


class EstimateFeeRequestSerializer(serializers.Serializer):
    """Request payload for fee estimation."""

    blockchain = serializers.ChoiceField(
        choices=BLOCKCHAIN_CHOICES,
    )
    from_address = serializers.CharField()
    to_address = serializers.CharField()
    amount = serializers.DecimalField(max_digits=30, decimal_places=18)


class TransactionStatusRequestSerializer(serializers.Serializer):
    """Request payload for transaction status lookup."""

    blockchain = serializers.ChoiceField(
        choices=BLOCKCHAIN_CHOICES,
    )
    tx_hash = serializers.CharField()


class GenerateAddressSerializer(serializers.Serializer):
    """Request payload for address generation."""

    blockchain = serializers.ChoiceField(
        choices=BLOCKCHAIN_CHOICES,
    )