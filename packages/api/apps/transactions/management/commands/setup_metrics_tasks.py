"""
Management command to set up periodic tasks for metrics collection.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Set up periodic tasks for metrics collection'

    def handle(self, *args, **options):
        """Set up all periodic tasks for metrics collection."""
        
        # Create interval schedules
        every_30_seconds, _ = IntervalSchedule.objects.get_or_create(
            every=30,
            period=IntervalSchedule.SECONDS,
        )
        
        every_minute, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        
        every_5_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )
        
        # Blockchain metrics collection task
        PeriodicTask.objects.get_or_create(
            name='Collect Blockchain Metrics',
            defaults={
                'task': 'apps.blockchain.tasks.collect_blockchain_metrics',
                'interval': every_30_seconds,
                'enabled': True,
            }
        )
        
        # Transaction queue metrics task
        PeriodicTask.objects.get_or_create(
            name='Collect Transaction Queue Metrics',
            defaults={
                'task': 'apps.blockchain.tasks.collect_transaction_queue_metrics',
                'interval': every_30_seconds,
                'enabled': True,
            }
        )
        
        # Wallet balance metrics task
        PeriodicTask.objects.get_or_create(
            name='Collect Wallet Balance Metrics',
            defaults={
                'task': 'apps.blockchain.tasks.collect_wallet_balance_metrics',
                'interval': every_minute,
                'enabled': True,
            }
        )
        
        # Blockchain health check task
        PeriodicTask.objects.get_or_create(
            name='Blockchain Health Check',
            defaults={
                'task': 'apps.blockchain.tasks.health_check_blockchain_nodes',
                'interval': every_5_minutes,
                'enabled': True,
            }
        )
        
        # Transaction status monitoring task (from existing setup)
        PeriodicTask.objects.get_or_create(
            name='Monitor Transaction Status',
            defaults={
                'task': 'apps.transactions.tasks.monitor_transaction_status',
                'interval': every_minute,
                'enabled': True,
            }
        )
        
        # Blockchain synchronization task (from existing setup)
        PeriodicTask.objects.get_or_create(
            name='Sync Blockchain Data',
            defaults={
                'task': 'apps.transactions.tasks.sync_blockchain_data',
                'interval': every_5_minutes,
                'enabled': True,
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up periodic tasks for metrics collection')
        )