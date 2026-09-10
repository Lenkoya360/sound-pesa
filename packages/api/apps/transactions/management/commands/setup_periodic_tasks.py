"""
Management command to set up periodic tasks for transaction processing.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json


class Command(BaseCommand):
    help = 'Set up periodic tasks for transaction processing and monitoring'
    
    def handle(self, *args, **options):
        """Set up all periodic tasks for the transaction system."""
        
        self.stdout.write('Setting up periodic tasks for transaction processing...')
        
        # Create schedules
        self._create_schedules()
        
        # Create periodic tasks
        self._create_periodic_tasks()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up all periodic tasks')
        )
    
    def _create_schedules(self):
        """Create interval and cron schedules."""
        
        # Every 30 seconds - for pending transaction monitoring
        self.every_30_seconds, _ = IntervalSchedule.objects.get_or_create(
            every=30,
            period=IntervalSchedule.SECONDS,
        )
        
        # Every 2 minutes - for transaction status updates
        self.every_2_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=2,
            period=IntervalSchedule.MINUTES,
        )
        
        # Every 5 minutes - for network fee rate updates
        self.every_5_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )
        
        # Every 10 minutes - for blockchain node monitoring
        self.every_10_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )
        
        # Every hour - for cleanup tasks
        self.every_hour, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )
        
        # Every 6 hours - for failed transaction retry
        self.every_6_hours, _ = IntervalSchedule.objects.get_or_create(
            every=6,
            period=IntervalSchedule.HOURS,
        )
        
        self.stdout.write('Created interval schedules')
    
    def _create_periodic_tasks(self):
        """Create all periodic tasks."""
        
        # Monitor pending transactions
        PeriodicTask.objects.update_or_create(
            name='Monitor Pending Transactions',
            defaults={
                'task': 'apps.transactions.tasks.monitor_pending_transactions',
                'interval': self.every_30_seconds,
                'enabled': True,
                'description': 'Monitor pending transactions and update their status'
            }
        )
        
        # Update network fee rates
        PeriodicTask.objects.update_or_create(
            name='Update Network Fee Rates',
            defaults={
                'task': 'apps.transactions.tasks.update_network_fee_rates',
                'interval': self.every_5_minutes,
                'enabled': True,
                'description': 'Update network fee rates for all blockchains'
            }
        )
        
        # Monitor blockchain nodes
        PeriodicTask.objects.update_or_create(
            name='Monitor Blockchain Nodes',
            defaults={
                'task': 'apps.transactions.tasks.monitor_blockchain_nodes',
                'interval': self.every_10_minutes,
                'enabled': True,
                'description': 'Monitor blockchain node health and synchronization'
            }
        )
        
        # Clean up expired estimates
        PeriodicTask.objects.update_or_create(
            name='Cleanup Expired Estimates',
            defaults={
                'task': 'apps.transactions.tasks.cleanup_expired_estimates',
                'interval': self.every_hour,
                'enabled': True,
                'description': 'Clean up expired transaction estimates'
            }
        )
        
        # Retry failed transactions
        PeriodicTask.objects.update_or_create(
            name='Retry Failed Transactions',
            defaults={
                'task': 'apps.transactions.tasks.retry_failed_transactions',
                'interval': self.every_6_hours,
                'enabled': True,
                'description': 'Retry failed transactions that might be recoverable'
            }
        )
        
        self.stdout.write('Created periodic tasks')
        
        # Display created tasks
        tasks = PeriodicTask.objects.filter(
            task__startswith='apps.transactions.tasks'
        )
        
        self.stdout.write('\nCreated periodic tasks:')
        for task in tasks:
            status = 'ENABLED' if task.enabled else 'DISABLED'
            self.stdout.write(f'  - {task.name}: {status}')
            self.stdout.write(f'    Task: {task.task}')
            if task.interval:
                self.stdout.write(f'    Interval: Every {task.interval.every} {task.interval.period}')
            self.stdout.write('')