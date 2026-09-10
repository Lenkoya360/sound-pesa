"""
Blockchain infrastructure models for Sound Pesa platform.

Tracks the nodes backing each supported chain, plus a raw transaction and
address ledger layer used by the blockchain adapters. Higher-level wallet and
transaction accounting lives in the ``wallets`` and ``transactions`` apps.
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

NETWORK_CHOICES = [
    ('mainnet', _('Mainnet')),
    ('testnet', _('Testnet')),
    ('regtest', _('Regtest')),
    ('goerli', _('Goerli')),
    ('westend', _('Westend')),
]

TRANSACTION_STATUS_CHOICES = [
    ('pending', _('Pending')),
    ('confirmed', _('Confirmed')),
    ('failed', _('Failed')),
    ('cancelled', _('Cancelled')),
]


class BlockchainNode(models.Model):
    """
    A blockchain node used by the platform, one per chain.
    """

    blockchain = models.CharField(
        _('blockchain'),
        max_length=20,
        choices=BLOCKCHAIN_CHOICES,
        unique=True,
    )

    network = models.CharField(_('network'), max_length=20, choices=NETWORK_CHOICES)

    rpc_url = models.URLField(_('RPC URL'))

    is_active = models.BooleanField(_('active'), default=True)
    is_synced = models.BooleanField(_('synchronized'), default=False)

    current_block_height = models.BigIntegerField(
        _('current block height'), default=0
    )
    peer_count = models.IntegerField(_('peer count'), default=0)

    last_checked = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Blockchain Node')
        verbose_name_plural = _('Blockchain Nodes')
        db_table = 'blockchain_nodes'
        ordering = ['blockchain']

    def __str__(self):
        return f"{self.get_blockchain_display()} ({self.network})"


class BlockchainTransaction(models.Model):
    """
    Raw blockchain transaction record captured by the adapters.
    """

    blockchain = models.CharField(
        _('blockchain'),
        max_length=20,
        choices=BLOCKCHAIN_CHOICES,
    )

    transaction_hash = models.CharField(
        _('transaction hash'), max_length=128, unique=True
    )

    from_address = models.CharField(_('from address'), max_length=128)
    to_address = models.CharField(_('to address'), max_length=128)

    amount = models.DecimalField(_('amount'), max_digits=30, decimal_places=18)

    fee = models.DecimalField(
        _('fee'),
        max_digits=30,
        decimal_places=18,
        null=True,
        blank=True,
    )

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending',
    )

    confirmations = models.IntegerField(_('confirmations'), default=0)
    block_height = models.BigIntegerField(_('block height'), null=True, blank=True)
    block_hash = models.CharField(
        _('block hash'), max_length=128, blank=True, null=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blockchain_transactions',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(_('confirmed at'), null=True, blank=True)

    class Meta:
        verbose_name = _('Blockchain Transaction')
        verbose_name_plural = _('Blockchain Transactions')
        db_table = 'blockchain_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'blockchain']),
            models.Index(fields=['transaction_hash']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_blockchain_display()} {self.transaction_hash[:16]}"


class BlockchainAddress(models.Model):
    """
    Generated blockchain address owned by a user.
    """

    blockchain = models.CharField(
        _('blockchain'),
        max_length=20,
        choices=BLOCKCHAIN_CHOICES,
    )

    address = models.CharField(_('address'), max_length=128)

    encrypted_private_key = models.TextField(_('encrypted private key'))

    is_active = models.BooleanField(_('active'), default=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blockchain_addresses',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Blockchain Address')
        verbose_name_plural = _('Blockchain Addresses')
        db_table = 'blockchain_addresses'
        unique_together = (('user', 'blockchain', 'address'),)
        indexes = [
            models.Index(fields=['user', 'blockchain']),
            models.Index(fields=['address']),
        ]

    def __str__(self):
        return f"{self.get_blockchain_display()} {self.address[:16]}"