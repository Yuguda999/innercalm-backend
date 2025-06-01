"""
Background scheduler for AI group management and other automated tasks.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from database import get_db
from services.ai_group_manager import ai_group_manager

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Background task scheduler for automated AI operations."""
    
    def __init__(self):
        self.running = False
        self.tasks = {}
        self.ai_management_interval = 3600  # Run every hour
        self.last_ai_run = None
        
    async def start(self):
        """Start the background scheduler."""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting background task scheduler")
        
        # Start the main scheduler loop
        asyncio.create_task(self._scheduler_loop())
        
    async def stop(self):
        """Stop the background scheduler."""
        self.running = False
        logger.info("Stopping background task scheduler")
        
    async def _scheduler_loop(self):
        """Main scheduler loop that runs background tasks."""
        while self.running:
            try:
                await self._run_scheduled_tasks()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Continue after error
                
    async def _run_scheduled_tasks(self):
        """Check and run any scheduled tasks that are due."""
        current_time = datetime.utcnow()
        
        # Check if AI group management should run
        if self._should_run_ai_management(current_time):
            await self._run_ai_group_management()
            
    def _should_run_ai_management(self, current_time: datetime) -> bool:
        """Check if AI group management should run."""
        if self.last_ai_run is None:
            return True
            
        time_since_last = current_time - self.last_ai_run
        return time_since_last.total_seconds() >= self.ai_management_interval
        
    async def _run_ai_group_management(self):
        """Run the AI group management cycle."""
        try:
            logger.info("Running scheduled AI group management")
            
            # Get database session
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Run AI group management
                results = await ai_group_manager.run_ai_group_management(db)
                
                self.last_ai_run = datetime.utcnow()
                logger.info(f"AI group management completed: {results}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error running scheduled AI group management: {e}")
            
    async def run_ai_management_now(self) -> Dict[str, Any]:
        """Manually trigger AI group management (for API calls)."""
        try:
            logger.info("Manually triggering AI group management")
            
            # Get database session
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Run AI group management
                results = await ai_group_manager.run_ai_group_management(db)
                
                self.last_ai_run = datetime.utcnow()
                logger.info(f"Manual AI group management completed: {results}")
                
                return results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in manual AI group management: {e}")
            raise
            
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self.running,
            "last_ai_run": self.last_ai_run.isoformat() if self.last_ai_run else None,
            "next_ai_run": (self.last_ai_run + timedelta(seconds=self.ai_management_interval)).isoformat() 
                          if self.last_ai_run else "pending",
            "ai_management_interval_hours": self.ai_management_interval / 3600
        }


# Global scheduler instance
scheduler = TaskScheduler()


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager to start/stop scheduler."""
    # Startup
    await scheduler.start()
    yield
    # Shutdown
    await scheduler.stop()
