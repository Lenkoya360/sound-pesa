"""
Wallet models for Sound Pesa platform.

Each authenticated user can hold one wallet per supported blockchain. Wallet
private keys are stored encrypted (via Vault in production) and balances are
tracked in a dedicated one-to-one companion record.
"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
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


class Wallet(models.Model):
    """
    A blockchain wallet belonging to a user.
    """

    BLOCKCHAIN_CHOICES = BLOCKCHAIN_CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallets',
    )

    blockchain = models.CharField(
        _('blockchain'),
        max_length=20,
        choices=BLOCKCHAIN_CHOICES,
    )

    address = models.CharField(
        _('address'),
        max_length=128,
        help_text=_('Public blockchain address'),
    )

    encrypted_private_key = models.TextField(
        _('encrypted private key'),
        help_text=_('Private key encrypted with Vault transit backend'),
    )

    label = models.CharField(
        _('label'),
        max_length=64,
        blank=True,
        help_text=_('Optional human-friendly wallet label'),
    )

    is_active = models.BooleanField(_('active'), default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')
        db_table = 'wallets'
        ordering = ['blockchain']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'blockchain'],
                name='unique_wallet_per_user_blockchain',
            ),
        ]

    def __str__(self):
        return f"{self.get_blockchain_display()} wallet for {self.user.email}"


class WalletBalance(models.Model):
    """
    Current balance snapshot for a wallet.

    Balances are stored as decimal strings to avoid floating-point precision
    loss when dealing with very small/large cryptocurrency amounts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    wallet = models.OneToOneField(
        Wallet,
        on_delete=models.CASCADE,
        related_name='balance',
    )

    balance = models.DecimalField(
        _('balance'),
        max_digits=36,
        decimal_places=18,
        default=Decimal('0'),
    )

    confirmed_balance = models.DecimalField(
        _('confirmed balance'),
        max_digits=36,
        decimal_places=18,
        default=Decimal('0'),
    )

    unconfirmed_balance = models.DecimalField(
        _('unconfirmed balance'),
        max_digits=36,
        decimal_places=18,
        default=Decimal('0'),
    )

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('wallet balance')
        verbose_name_plural = _('wallet balances')
        db_table = 'wallet_balances'

    def __str__(self):
        return f"{self.balance} for wallet {self.wallet.id}"


class WalletTransaction(models.Model):
    """
    Transaction history entry for a wallet.
    """

    TRANSACTION_TYPE_CHOICES = [
        ('send', _('Send')),
        ('receive', _('Receive')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
    )

    transaction_type = models.CharField(
        _('transaction type'),
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
    )

    amount = models.DecimalField(_('amount'), max_digits=36, decimal_places=18)

    fee = models.DecimalField(
        _('fee'),
        max_digits=36,
        decimal_places=18,
        null=True,
        blank=True,
    )

    from_address = models.CharField(_('from address'), max_length=128)
    to_address = models.CharField(_('to address'), max_length=128)

    transaction_hash = models.CharField(
        _('transaction hash'),
        max_length=128,
        blank=True,
        null=True,
    )

    block_height = models.BigIntegerField(_('block height'), null=True, blank=True)
    confirmations = models.IntegerField(_('confirmations'), default=0)

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(_('confirmed at'), null=True, blank=True)

    class Meta:
        verbose_name = _('wallet transaction')
        verbose_name_plural = _('wallet transactions')
        db_table = 'wallet_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'status']),
            models.Index(fields=['transaction_hash']),
        ]

    def __str__(self):
        return f"{self.transaction_type} {self.amount} on wallet {self.wallet.id}"


class WalletAddress(models.Model):
    """
    Additional addresses generated for a wallet (e.g. change addresses).

    Kept separate from ``Wallet`` so a wallet can own several derived
    addresses over time without losing the primary one.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='addresses',
    )

    address = models.CharField(_('address'), max_length=128)

    is_used = models.BooleanField(_('used'), default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(_('used at'), null=True, blank=True)

    class Meta:
        verbose_name = _('wallet address')
        verbose_name_plural = _('wallet addresses')
        db_table = 'wallet_addresses'
        constraints = [
            models.UniqueConstraint(
                fields=['wallet', 'address'],
                name='unique_address_per_wallet',
            ),
        ]

    def __str__(self):
        return f"{self.address} ({self.wallet.id})"