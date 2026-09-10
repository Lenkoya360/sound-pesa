"""
User and profile models for Sound Pesa platform.
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model for the Sound Pesa platform.

    Uses email as the primary login identifier while keeping the standard
    Django authentication machinery (username/password) intact.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    KYC_STATUS_CHOICES = [
        ('not_started', _('Not Started')),
        ('pending', _('Pending Verification')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    kyc_status = models.CharField(
        _('KYC status'),
        max_length=20,
        choices=KYC_STATUS_CHOICES,
        default='not_started',
    )

    two_factor_enabled = models.BooleanField(
        _('two-factor authentication enabled'),
        default=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the user's full name."""
        name = f"{self.profile.first_name} {self.profile.last_name}".strip()
        return name or self.username


class UserProfile(models.Model):
    """
    Extended profile information for a user.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )

    first_name = models.CharField(_('first name'), max_length=50, blank=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True)

    phone_number = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        help_text=_('Phone number in E.164 format, e.g. +254712345678'),
    )

    country = models.CharField(
        _('country'),
        max_length=2,
        blank=True,
        help_text=_('ISO 3166-1 alpha-2 country code'),
    )

    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile for {self.user.email}"

    @property
    def full_name(self):
        """Return the profile owner's full name."""
        return f"{self.first_name} {self.last_name}".strip()