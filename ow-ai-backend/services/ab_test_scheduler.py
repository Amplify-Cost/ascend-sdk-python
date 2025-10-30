"""
A/B Test Auto-Completion Scheduler
Background task to automatically complete expired tests and determine winners.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging
import threading
import time

logger = logging.getLogger(__name__)


class ABTestScheduler:
    """Background scheduler for A/B test auto-completion"""

    def __init__(self, db_session_factory):
        """
        Initialize the scheduler.

        Args:
            db_session_factory: Callable that returns a new database session
        """
        self.db_session_factory = db_session_factory
        self.running = False
        self.thread = None

    def start(self, check_interval_minutes: int = 60):
        """
        Start the background scheduler.

        Args:
            check_interval_minutes: How often to check for expired tests (default: 60 minutes)
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._run_scheduler,
            args=(check_interval_minutes,),
            daemon=True
        )
        self.thread.start()
        logger.info(f"✅ A/B Test Scheduler started (checking every {check_interval_minutes} minutes)")

    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🛑 A/B Test Scheduler stopped")

    def _run_scheduler(self, check_interval_minutes: int):
        """Internal method to run the scheduler loop"""
        while self.running:
            try:
                self.check_and_complete_tests()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

            # Sleep for the specified interval
            time.sleep(check_interval_minutes * 60)

    def check_and_complete_tests(self):
        """Check for expired tests and auto-complete them"""
        db = self.db_session_factory()
        try:
            # Find tests that should be completed
            expired_tests = self._find_expired_tests(db)

            logger.info(f"🔍 Found {len(expired_tests)} expired A/B tests to complete")

            for test in expired_tests:
                self._auto_complete_test(db, test)

        except Exception as e:
            logger.error(f"Error checking expired tests: {e}")
        finally:
            db.close()

    def _find_expired_tests(self, db: Session) -> List[Dict[str, Any]]:
        """
        Find tests that have expired and should be auto-completed.

        Args:
            db: Database session

        Returns:
            List of expired test data
        """
        try:
            tests = db.execute(text("""
                SELECT
                    test_id, test_name, created_at, duration_hours,
                    variant_a_performance, variant_b_performance,
                    sample_size, status
                FROM ab_tests
                WHERE status = 'running'
                AND created_at + (duration_hours * INTERVAL '1 hour') <= NOW()
                ORDER BY created_at ASC
            """)).fetchall()

            return [
                {
                    "test_id": test.test_id,
                    "test_name": test.test_name,
                    "created_at": test.created_at,
                    "duration_hours": test.duration_hours,
                    "variant_a_performance": float(test.variant_a_performance or 0),
                    "variant_b_performance": float(test.variant_b_performance or 0),
                    "sample_size": test.sample_size or 0,
                    "status": test.status
                }
                for test in tests
            ]

        except Exception as e:
            logger.error(f"Error finding expired tests: {e}")
            return []

    def _auto_complete_test(self, db: Session, test_data: Dict[str, Any]):
        """
        Auto-complete an expired test.

        Args:
            db: Database session
            test_data: Test information
        """
        try:
            test_id = test_data["test_id"]
            test_name = test_data["test_name"]

            logger.info(f"⏰ Auto-completing expired test: {test_name} ({test_id})")

            # Calculate real metrics from alerts
            from services.ab_test_alert_router import ABTestAlertRouter
            router = ABTestAlertRouter(db)
            metrics = router.calculate_ab_test_metrics(test_id)

            # Determine winner
            winner = self._determine_winner(test_data, metrics)

            # Calculate confidence based on sample size
            sample_size = metrics.get("comparison", {}).get("sample_size", test_data["sample_size"])
            confidence = self._calculate_confidence(sample_size)

            # Calculate statistical significance
            significance = "high" if confidence >= 90 else ("medium" if confidence >= 70 else "low")

            # Update test record
            db.execute(text("""
                UPDATE ab_tests
                SET status = 'completed',
                    completed_at = NOW(),
                    winner = :winner,
                    confidence_level = :confidence,
                    statistical_significance = :significance,
                    progress_percentage = 100,
                    updated_at = NOW()
                WHERE test_id = :test_id
            """), {
                "test_id": test_id,
                "winner": winner,
                "confidence": confidence,
                "significance": significance
            })

            db.commit()

            logger.info(
                f"✅ Auto-completed test {test_name}: "
                f"Winner = {winner}, "
                f"Confidence = {confidence}%, "
                f"Sample size = {sample_size}"
            )

            # TODO: Send notification to user (email, slack, etc.)
            self._send_completion_notification(test_data, winner, confidence, sample_size)

        except Exception as e:
            logger.error(f"Error auto-completing test {test_data['test_id']}: {e}")
            db.rollback()

    def _determine_winner(
        self,
        test_data: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> str:
        """
        Determine the winning variant based on performance metrics.

        Args:
            test_data: Test information
            metrics: Calculated metrics from real alerts

        Returns:
            'variant_a' or 'variant_b'
        """
        try:
            if metrics and "variant_a" in metrics and "variant_b" in metrics:
                # Use real metrics
                a_score = metrics["variant_a"]["performance_score"]
                b_score = metrics["variant_b"]["performance_score"]
            else:
                # Fallback to stored values
                a_score = test_data["variant_a_performance"]
                b_score = test_data["variant_b_performance"]

            # Variant B wins if it's better (or tied)
            return "variant_b" if b_score >= a_score else "variant_a"

        except Exception as e:
            logger.error(f"Error determining winner: {e}")
            # Default to variant_a on error
            return "variant_a"

    def _calculate_confidence(self, sample_size: int) -> int:
        """
        Calculate confidence level based on sample size.

        Args:
            sample_size: Number of samples (alerts evaluated)

        Returns:
            Confidence level (0-100)
        """
        if sample_size >= 500:
            return 99
        elif sample_size >= 300:
            return 95
        elif sample_size >= 200:
            return 90
        elif sample_size >= 100:
            return 85
        elif sample_size >= 50:
            return 75
        elif sample_size >= 25:
            return 65
        elif sample_size >= 10:
            return 55
        else:
            return max(40, min(50, 40 + sample_size * 2))

    def _send_completion_notification(
        self,
        test_data: Dict[str, Any],
        winner: str,
        confidence: int,
        sample_size: int
    ):
        """
        Send notification about test completion.

        Args:
            test_data: Test information
            winner: Winning variant
            confidence: Confidence level
            sample_size: Number of samples
        """
        # TODO: Implement actual notification system (email, Slack, etc.)
        logger.info(
            f"📧 Notification: Test '{test_data['test_name']}' completed. "
            f"Winner: {winner}, Confidence: {confidence}%, Samples: {sample_size}"
        )
        # Future: Send email, Slack message, or create in-app notification


# Global scheduler instance
_scheduler_instance = None


def get_scheduler(db_session_factory) -> ABTestScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ABTestScheduler(db_session_factory)
    return _scheduler_instance


def start_scheduler(db_session_factory, check_interval_minutes: int = 60):
    """Start the global scheduler"""
    scheduler = get_scheduler(db_session_factory)
    scheduler.start(check_interval_minutes)
    return scheduler


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
        _scheduler_instance = None
