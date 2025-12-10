"""
Django management command to run the notification scheduler
Usage: python manage.py run_scheduler
"""
from django.core.management.base import BaseCommand
from radgestmat.scheduler import start_scheduler, stop_scheduler


class Command(BaseCommand):
    help = 'Start the APScheduler background job scheduler for notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stop',
            action='store_true',
            help='Stop the scheduler instead of starting it',
        )

    def handle(self, *args, **options):
        if options['stop']:
            self.stdout.write(
                self.style.WARNING('Stopping scheduler...')
            )
            stop_scheduler()
            self.stdout.write(
                self.style.SUCCESS('Scheduler stopped')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Starting notification scheduler...')
            )
            try:
                scheduler = start_scheduler()
                self.stdout.write(
                    self.style.SUCCESS('✓ Scheduler started successfully')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {len(scheduler.get_jobs())} jobs registered')
                )
                
                # Display registered jobs
                self.stdout.write('\nRegistered Jobs:')
                for job in scheduler.get_jobs():
                    self.stdout.write(f'  - {job.id}: {job.name}')
                    self.stdout.write(f'    Next run: {job.next_run_time}')
                
                # Keep running
                import time
                self.stdout.write('\n' + self.style.SUCCESS(
                    '✓ Scheduler is running. Press Ctrl+C to stop.'
                ))
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.stdout.write('\n' + self.style.WARNING(
                        'Received interrupt. Stopping scheduler...'
                    ))
                    stop_scheduler()
                    self.stdout.write(self.style.SUCCESS('Scheduler stopped'))
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error starting scheduler: {e}')
                )
                raise
