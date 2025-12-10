"""
APScheduler configuration and background job runner for RadGestMat
Handles automatic notification scheduling and monitoring
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from django.conf import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def start_scheduler():
    """
    Start the background scheduler for notification jobs
    Called from Django management command
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.info("Scheduler is already running")
        return scheduler
    
    try:
        # Configure executors
        executors = {
            'default': ThreadPoolExecutor(max_workers=3),
            'processpool': ProcessPoolExecutor(max_workers=1)
        }
        
        # Configure job defaults
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 600,  # 10 minutes grace period
        }
        
        # Create scheduler
        scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults,
            timezone=settings.TIME_ZONE,
        )
        
        # Register jobs
        _register_jobs()
        
        # Start scheduler
        scheduler.start()
        logger.info("APScheduler started successfully")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("APScheduler stopped")


def _register_jobs():
    """Register all notification scheduling jobs"""
    from assets.scheduler_jobs import (
        check_court_terme_reminders,
        check_moyen_terme_reminders,
        check_long_terme_reminders,
        check_overdue_materials,
        cleanup_old_notifications,
    )
    
    # Court terme (Short term): Check every 30 minutes
    # For loans < 4 hours, remind at 2 hours before return
    scheduler.add_job(
        func=check_court_terme_reminders,
        trigger=CronTrigger(minute='*/30'),
        id='check_court_terme_reminders',
        name='Check court terme (short-term) loan reminders',
        replace_existing=True,
    )
    logger.info("Registered job: check_court_terme_reminders (every 30 min)")
    
    # Moyen terme (Medium term): Check twice daily
    # For loans 4-24 hours, remind at 2 hours before return
    scheduler.add_job(
        func=check_moyen_terme_reminders,
        trigger=CronTrigger(hour='*/12'),
        id='check_moyen_terme_reminders',
        name='Check moyen terme (medium-term) loan reminders',
        replace_existing=True,
    )
    logger.info("Registered job: check_moyen_terme_reminders (every 12 hours)")
    
    # Long terme (Long term): Check daily at 8 AM
    # For loans > 24 hours, remind at J-2 and J-1
    scheduler.add_job(
        func=check_long_terme_reminders,
        trigger=CronTrigger(hour=8, minute=0),
        id='check_long_terme_reminders',
        name='Check long terme (long-term) loan reminders',
        replace_existing=True,
    )
    logger.info("Registered job: check_long_terme_reminders (daily at 8:00 AM)")
    
    # Check for overdue materials: Every 15 minutes
    scheduler.add_job(
        func=check_overdue_materials,
        trigger=CronTrigger(minute='*/15'),
        id='check_overdue_materials',
        name='Check for overdue materials',
        replace_existing=True,
    )
    logger.info("Registered job: check_overdue_materials (every 15 min)")
    
    # Cleanup old notifications: Daily at 2 AM
    # Remove old notification logs older than 90 days
    scheduler.add_job(
        func=cleanup_old_notifications,
        trigger=CronTrigger(hour=2, minute=0),
        id='cleanup_old_notifications',
        name='Cleanup old notification logs',
        replace_existing=True,
    )
    logger.info("Registered job: cleanup_old_notifications (daily at 2:00 AM)")


def get_scheduler_status():
    """Get current scheduler status"""
    global scheduler
    
    if scheduler is None:
        return {
            'running': False,
            'jobs': []
        }
    
    return {
        'running': scheduler.running,
        'jobs': [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time),
            }
            for job in scheduler.get_jobs()
        ]
    }


def restart_scheduler():
    """Restart the scheduler"""
    try:
        stop_scheduler()
        start_scheduler()
        logger.info("Scheduler restarted successfully")
    except Exception as e:
        logger.error(f"Error restarting scheduler: {e}")
        raise
