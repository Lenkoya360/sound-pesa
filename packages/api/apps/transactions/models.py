"""
Transaction models for Sound Pesa platform.

A transaction moves funds from a user wallet to an external address across one
of the supported blockchains. Full-fidelity accounting is kept through
audit logs, fee estimates and distributed transaction locks to guarantee
at-most-once broadcasting.
"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import DecimalValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

BLOCKCHAIN_CHOICES = [
    ('bitcoin', _('Bitcoin')),
    ('ethereum', _('Ethereum')),
    ('cardano', _('Cardano')),
    ('polkadot', _('Polkadot')),
]

TRANSACTION_STATUS_CHOICES = [
    ('pending', _('Pending')),
    ('confirmed', _('Confirmed')),
    ('failed', _('Failed')),
    ('cancelled', _('Cancelled')),
]

CONGESTION_CHOICES = [
    ('low', _('Low')),
    ('medium', _('Medium')),
    ('high', _('High')),
]

FEE_PRIORITY_CHOICES = [
    ('low', _('Low Priority')),
    ('medium', _('Medium Priority')),
    ('high', _('High Priority')),
]

AUDIT_ACTION_CHOICES = [
    ('created', _('Transaction Created')),
    ('validated', _('Transaction Validated')),
    ('signed', _('Transaction Signed')),
    ('broadcasted', _('Transaction Broadcasted')),
    ('confirmed', _('Transaction Confirmed')),
    ('failed', _('Transaction Failed')),
    ('cancelled', _('Transaction Cancelled')),
    ('retry', _('Transaction Retry')),
    ('status_updated', _('Status Updated')),
]


class Transaction(models.Model):
    """
    A pending, broadcasted or settled cryptocurrency transaction.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
    )

    from_wallet = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.CASCADE,
        related_name='outgoing_transactions',
    )

    to_address = models.CharField(_('destination address'), max_length=255)

    blockchain = models.CharField(
        _('blockchain'),
        max_length=20,
        choices=BLOCKCHAIN_CHOICES,
    )

    amount = models.DecimalField(
        _('amount'),
        max_digits=36,
        decimal_places=18,
        validators=[
            DecimalValidator(max_digits=36, decimal_places=18),
            MinValueValidator(Decimal('1E-18')),
        ],
    )

    fee = models.DecimalField(
        _('fee'),
        max_digits=36,
        decimal_places=18,
        default=Decimal('0E-18'),
        validators=[DecimalValidator(max_digits=36, decimal_places=18)],
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending',
    )

    transaction_hash = models.CharField(
        _('transaction hash'),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    block_height = models.BigIntegerField(_('block height'), null=True, blank=True)
    confirmations = models.IntegerField(_('confirmations'), default=0)

    # Ethereum-specific fields
    gas_limit = models.BigIntegerField(_('gas limit'), null=True, blank=True)
    gas_price = models.DecimalField(
        _('gas price'),
        max_digits=36,
        decimal_places=18,
        null=True,
        blank=True,
        validators=[DecimalValidator(max_digits=36, decimal_places=18)],
    )
    nonce = models.BigIntegerField(_('nonce'), null=True, blank=True)

    # Bitcoin-specific fields
    utxo_inputs = models.JSONField(_('UTXO inputs'), null=True, blank=True)
    change_address = models.CharField(
        _('change address'), max_length=255, blank=True, null=True
    )

    correlation_id = models.UUIDField(db_index=True, default=uuid.uuid4)

    retry_count = models.IntegerField(_('retry count'), default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(_('error message'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(_('confirmed at'), null=True, blank=True)

    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        db_table = 'transaction'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
            models.Index(fields=['from_wallet', 'status']),
            models.Index(fields=['blockchain', 'status']),
            models.Index(fields=['transaction_hash']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['block_height']),
            models.Index(fields=['confirmations']),
        ]

    def __str__(self):
        return f"{self.get_blockchain_display()} {self.get_status_display()} {self.amount}"


class TransactionEstimate(models.Model):
    """
    A fee/confirmation estimate produced before a transaction is created.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transaction_estimates',
        null=True,
        blank=True,
    )

    blockchain = models.CharField(
        _('blockchain'),
        max_length=20,
        choices=BLOCKCHAIN_CHOICES,
    )

    amount = models.DecimalField(
        _('amount'),
        max_digits=36,
        decimal_places=18,
        validators=[DecimalValidator(max_digits=36, decimal_places=18)],
    )

    estimated_fee = models.DecimalField(
        _('estimated fee'),
        max_digits=36,
        decimal_places=18,
        validators=[DecimalValidator(max_digits=36, decimal_places=18)],
    )

    fee_priority = models.CharField(
        _('fee priority'),
        max_length=10,
        choices=FEE_PRIORITY_CHOICES,
        default='medium',
    )

    estimated_confirmation_time = models.IntegerField(
        _('estimated confirmation time (minutes)')
    )

    network_congestion = models.CharField(
        _('network congestion'),
        max_length=10,
        choices=CONGESTION_CHOICES,
    )

    # Ethereum-specific
    gas_limit = models.BigIntegerField(_('gas limit'), null=True, blank=True)
    gas_price = models.DecimalField(
        _('gas price'),
        max_digits=36,
        decimal_places=18,
        null=True,
        blank=True,
        validators=[DecimalValidator(max_digits=36, decimal_places=18)],
    )

    # Bitcoin-specific
    sat_per_byte = models.DecimalField(
        _('satoshis per byte'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    correlation_id = models.UUIDField(db_index=True, default=uuid.uuid4)

    is_used = models.BooleanField(_('used'), default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))

    class Meta:
        verbose_name = _('Transaction Estimate')
        verbose_name_plural = _('Transaction Estimates')
        db_table = 'transaction_estimate'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['blockchain', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_used', 'created_at']),
        ]

    def __str__(self):
        return f"Estimate for {self.amount} {self.blockchain} ({self.fee_priority})"

    @property
    def is_expired(self):
        """Whether this estimate is past its expiry time."""
        return timezone.now() > self.expires_at


class TransactionAuditLog(models.Model):
    """
    Immutable, append-only audit trail for a transaction lifecycle.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    correlation_id = models.UUIDField(db_index=True)

    action = models.CharField(
        _('action'),
        max_length=20,
        choices=AUDIT_ACTION_CHOICES,
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)

    blockchain_response = models.JSONField(null=True, blank=True)
    error_details = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(blank=True, default=dict)

    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Transaction Audit Log')
        verbose_name_plural = _('Transaction Audit Logs')
        db_table = 'transaction_audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction', 'created_at']),
            models.Index(fields=['correlation_id', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.action} for transaction {self.transaction_id}"


class TransactionLock(models.Model):
    """
    Distributed lock guarding a transaction against duplicate broadcasting.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='lock',
    )

    locked_by = models.CharField(_('locked by'), max_length=255)
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))

    class Meta:
        verbose_name = _('Transaction Lock')
        verbose_name_plural = _('Transaction Locks')
        db_table = 'transaction_lock'
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['locked_by']),
        ]

    def __str__(self):
        return f"Lock on {self.transaction_id} by {self.locked_by}"


class NetworkFeeRate(models.Model):
    """
    Current fee rates for a blockchain network, refreshed periodically.
    """

    blockchain = models.CharField(
        _('blockchain'),
        max_length=20,
        choices=BLOCKCHAIN_CHOICES,
        unique=True,
    )

    low_fee_rate = models.DecimalField(
        _('low fee rate'),
        max_digits=36,
        decimal_places=18,
        validators=[DecimalValidator(max_digits=36, decimal_places=18)],
    )

    medium_fee_rate = models.DecimalField(
        _('medium fee rate'),
        max_digits=36,
        decimal_places=18,
        validators=[DecimalValidator(max_digits=36, decimal_places=18)],
    )

    high_fee_rate = models.DecimalField(
        _('high fee rate'),
        max_digits=36,
        decimal_places=18,
        validators=[DecimalValidator(max_digits=36, decimal_places=18)],
    )

    mempool_size = models.BigIntegerField(_('mempool size'), default=0)

    average_confirmation_time = models.IntegerField(
        _('average confirmation time (minutes)'), default=0
    )

    congestion_level = models.CharField(
        _('congestion level'),
        max_length=10,
        choices=CONGESTION_CHOICES,
        default='medium',
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Network Fee Rate')
        verbose_name_plural = _('Network Fee Rates')
        db_table = 'network_fee_rate'

    def __str__(self):
        return f"{self.get_blockchain_display()} fee rates"