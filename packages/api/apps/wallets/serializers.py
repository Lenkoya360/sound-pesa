"""
Serializers for wallet management.
"""
from rest_framework import serializers
from .models import Wallet, WalletBalance, WalletTransaction, WalletAddress


class WalletBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer for wallet balance information.
    """
    class Meta:
        model = WalletBalance
        fields = ('balance', 'confirmed_balance', 'unconfirmed_balance', 'last_updated')
        read_only_fields = ('balance', 'confirmed_balance', 'unconfirmed_balance', 'last_updated')


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for wallet information.
    """
    balance = WalletBalanceSerializer(read_only=True)
    blockchain_display = serializers.CharField(source='get_blockchain_display', read_only=True)
    
    class Meta:
        model = Wallet
        fields = ('id', 'blockchain', 'blockchain_display', 'address', 'is_active', 
                 'created_at', 'updated_at', 'balance')
        read_only_fields = ('id', 'address', 'created_at', 'updated_at')


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for wallet transaction history.
    """
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    blockchain = serializers.CharField(source='wallet.blockchain', read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = ('id', 'blockchain', 'transaction_type', 'transaction_type_display',
                 'amount', 'fee', 'from_address', 'to_address', 'transaction_hash',
                 'block_height', 'confirmations', 'status', 'status_display',
                 'created_at', 'confirmed_at')
        read_only_fields = ('id', 'transaction_hash', 'block_height', 'confirmations',
                           'created_at', 'confirmed_at')


class WalletCreationSerializer(serializers.Serializer):
    """
    Serializer for wallet creation requests.
    """
    blockchain = serializers.ChoiceField(choices=Wallet.BLOCKCHAIN_CHOICES)
    
    def validate_blockchain(self, value):
        """
        Validate that user doesn't already have a wallet for this blockchain.
        """
        user = self.context['request'].user
        if Wallet.objects.filter(user=user, blockchain=value).exists():
            raise serializers.ValidationError(
                f"User already has a {value} wallet."
            )
        return value


class WalletAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for wallet addresses.
    """
    class Meta:
        model = WalletAddress
        fields = ('address', 'is_used', 'created_at', 'used_at')
        read_only_fields = ('is_used', 'created_at', 'used_at')


class WalletSummarySerializer(serializers.Serializer):
    """
    Serializer for wallet summary across all blockchains.
    """
    total_wallets = serializers.IntegerField(read_only=True)
    active_wallets = serializers.IntegerField(read_only=True)
    blockchains = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    total_balance_usd = serializers.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        read_only=True
    )
    last_transaction = serializers.DateTimeField(read_only=True)