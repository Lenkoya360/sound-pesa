"""
Transaction serializers for Sound Pesa platform.
"""
from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from .models import Transaction, TransactionEstimate, TransactionAuditLog
from apps.wallets.models import Wallet
from apps.blockchain.adapters.factory import BlockchainAdapterFactory


class TransactionEstimateRequestSerializer(serializers.Serializer):
    """
    Serializer for transaction fee estimation requests.
    """
    from_wallet_id = serializers.UUIDField()
    to_address = serializers.CharField(max_length=255)
    amount = serializers.CharField(max_length=50)
    fee_priority = serializers.ChoiceField(
        choices=['low', 'medium', 'high'],
        default='medium'
    )
    
    def validate_from_wallet_id(self, value):
        """Validate that the wallet exists and belongs to the user."""
        user = self.context['request'].user
        try:
            wallet = Wallet.objects.get(id=value, user=user, is_active=True)
            return value
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not found or not accessible.")
    
    def validate_amount(self, value):
        """Validate amount format and range."""
        try:
            amount = Decimal(value)
            if amount <= 0:
                raise serializers.ValidationError("Amount must be greater than zero.")
            if amount > Decimal('1000000'):  # Max transaction limit
                raise serializers.ValidationError("Amount exceeds maximum transaction limit.")
            return str(amount)
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Invalid amount format.")
    
    def validate(self, attrs):
        """Cross-field validation."""
        user = self.context['request'].user
        wallet = Wallet.objects.get(id=attrs['from_wallet_id'], user=user)
        
        # Validate address format for the blockchain
        try:
            adapter = BlockchainAdapterFactory.get_adapter(wallet.blockchain)
            if not adapter.validate_address(attrs['to_address']):
                raise serializers.ValidationError({
                    'to_address': f"Invalid {wallet.blockchain} address format."
                })
        except Exception as e:
            raise serializers.ValidationError({
                'blockchain': f"Blockchain adapter error: {str(e)}"
            })
        
        attrs['blockchain'] = wallet.blockchain
        return attrs


class TransactionEstimateSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction estimate responses.
    """
    class Meta:
        model = TransactionEstimate
        fields = [
            'id', 'blockchain', 'amount', 'estimated_fee', 'fee_priority',
            'estimated_confirmation_time', 'network_congestion',
            'gas_limit', 'gas_price', 'sat_per_byte', 'expires_at'
        ]
        read_only_fields = ['id', 'expires_at']


class TransactionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new transactions.
    """
    from_wallet_id = serializers.UUIDField()
    to_address = serializers.CharField(max_length=255)
    amount = serializers.CharField(max_length=50)
    fee_priority = serializers.ChoiceField(
        choices=['low', 'medium', 'high'],
        default='medium'
    )
    estimate_id = serializers.UUIDField(required=False)
    
    def validate_from_wallet_id(self, value):
        """Validate that the wallet exists and belongs to the user."""
        user = self.context['request'].user
        try:
            wallet = Wallet.objects.get(id=value, user=user, is_active=True)
            return value
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not found or not accessible.")
    
    def validate_amount(self, value):
        """Validate amount format and range."""
        try:
            amount = Decimal(value)
            if amount <= 0:
                raise serializers.ValidationError("Amount must be greater than zero.")
            if amount > Decimal('1000000'):  # Max transaction limit
                raise serializers.ValidationError("Amount exceeds maximum transaction limit.")
            return str(amount)
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Invalid amount format.")
    
    def validate_estimate_id(self, value):
        """Validate that the estimate exists and is not expired."""
        if value:
            try:
                estimate = TransactionEstimate.objects.get(id=value)
                if estimate.is_expired:
                    raise serializers.ValidationError("Transaction estimate has expired.")
                if estimate.is_used:
                    raise serializers.ValidationError("Transaction estimate has already been used.")
                return value
            except TransactionEstimate.DoesNotExist:
                raise serializers.ValidationError("Transaction estimate not found.")
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        user = self.context['request'].user
        wallet = Wallet.objects.get(id=attrs['from_wallet_id'], user=user)
        
        # Validate address format for the blockchain
        try:
            adapter = BlockchainAdapterFactory.get_adapter(wallet.blockchain)
            if not adapter.validate_address(attrs['to_address']):
                raise serializers.ValidationError({
                    'to_address': f"Invalid {wallet.blockchain} address format."
                })
        except Exception as e:
            raise serializers.ValidationError({
                'blockchain': f"Blockchain adapter error: {str(e)}"
            })
        
        # Check wallet balance (basic validation)
        if hasattr(wallet, 'balance'):
            available_balance = wallet.balance.confirmed_balance
            required_amount = Decimal(attrs['amount'])
            
            if available_balance < required_amount:
                raise serializers.ValidationError({
                    'amount': "Insufficient balance for this transaction."
                })
        
        attrs['blockchain'] = wallet.blockchain
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction responses.
    """
    from_wallet_address = serializers.CharField(source='from_wallet.address', read_only=True)
    blockchain_display = serializers.CharField(source='get_blockchain_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'from_wallet', 'from_wallet_address', 'to_address',
            'blockchain', 'blockchain_display', 'amount', 'fee',
            'status', 'status_display', 'transaction_hash',
            'block_height', 'confirmations', 'correlation_id',
            'retry_count', 'error_message', 'created_at',
            'updated_at', 'confirmed_at'
        ]
        read_only_fields = [
            'id', 'from_wallet_address', 'blockchain_display',
            'status_display', 'transaction_hash', 'block_height',
            'confirmations', 'correlation_id', 'retry_count',
            'error_message', 'created_at', 'updated_at', 'confirmed_at'
        ]


class TransactionDetailSerializer(TransactionSerializer):
    """
    Detailed transaction serializer with additional fields.
    """
    audit_logs = serializers.SerializerMethodField()
    
    class Meta(TransactionSerializer.Meta):
        fields = TransactionSerializer.Meta.fields + [
            'gas_limit', 'gas_price', 'nonce', 'utxo_inputs',
            'change_address', 'last_retry_at', 'audit_logs'
        ]
    
    def get_audit_logs(self, obj):
        """Get recent audit logs for the transaction."""
        recent_logs = obj.audit_logs.all()[:10]  # Last 10 logs
        return TransactionAuditLogSerializer(recent_logs, many=True).data


class TransactionAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction audit logs.
    """
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = TransactionAuditLog
        fields = [
            'id', 'action', 'action_display', 'previous_status',
            'new_status', 'message', 'created_at'
        ]
        read_only_fields = ['id', 'action_display', 'created_at']


class TransactionStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for transaction status updates.
    """
    transaction_hash = serializers.CharField(max_length=255, required=False)
    block_height = serializers.IntegerField(required=False)
    confirmations = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(
        choices=['pending', 'confirmed', 'failed', 'cancelled'],
        required=False
    )
    error_message = serializers.CharField(max_length=1000, required=False)
    
    def validate(self, attrs):
        """Validate status update data."""
        if attrs.get('status') == 'confirmed':
            if not attrs.get('transaction_hash'):
                raise serializers.ValidationError({
                    'transaction_hash': 'Transaction hash is required for confirmed transactions.'
                })
        
        if attrs.get('status') == 'failed':
            if not attrs.get('error_message'):
                raise serializers.ValidationError({
                    'error_message': 'Error message is required for failed transactions.'
                })
        
        return attrs


class TransactionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for transaction lists.
    """
    from_wallet_address = serializers.CharField(source='from_wallet.address', read_only=True)
    blockchain_display = serializers.CharField(source='get_blockchain_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'from_wallet_address', 'to_address', 'blockchain',
            'blockchain_display', 'amount', 'fee', 'status',
            'status_display', 'transaction_hash', 'confirmations',
            'created_at', 'confirmed_at'
        ]
        read_only_fields = fields