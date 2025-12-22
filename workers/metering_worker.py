"""
Phase 10B: Metering Background Worker

Processes usage events from Redis queue to PostgreSQL.
Runs every 5 minutes (configurable).

Features:
- Distributed locking to prevent duplicate processing
- Batch processing for efficiency
- Automatic retry on failure
- Health metrics for monitoring

Usage:
    worker = MeteringWorker()
    await worker.start()  # Runs in background

Compliance: SOC 2 CC6.1
Engineer: OW-KAI Platform Engineering Team
Version: Phase 10B
Date: 2025-12-21
"""

import os
import asyncio
import logging
import signal
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
except ImportError:
    # Fallback for older redis versions
    from redis import asyncio as redis

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
WORKER_INTERVAL_SECONDS = int(os.environ.get("METERING_WORKER_INTERVAL", "300"))  # 5 minutes
LOCK_KEY = "billing:metering_worker:lock"
LOCK_TTL_SECONDS = 600  # 10 minutes
BATCH_SIZE = int(os.environ.get("METERING_BATCH_SIZE", "1000"))

# Health check keys
HEALTH_KEY = "billing:metering_worker:health"
LAST_RUN_KEY = "billing:metering_worker:last_run"


# =============================================================================
# METERING WORKER
# =============================================================================

class MeteringWorker:
    """
    Background worker for processing usage events.

    Responsibilities:
    1. Pop events from Redis queue
    2. Aggregate and store in PostgreSQL
    3. Update usage counters
    4. Report to Stripe (optional)

    Designed for horizontal scaling:
    - Uses Redis distributed lock
    - Only one instance processes at a time
    - Other instances wait or skip
    """

    def __init__(self):
        self._running = False
        self._redis: Optional[redis.Redis] = None
        self._task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        if self._redis is None:
            self._redis = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis

    async def _acquire_lock(self) -> bool:
        """
        Acquire distributed lock for worker.

        Returns True if lock acquired, False otherwise.
        Lock auto-expires after LOCK_TTL_SECONDS.
        """
        try:
            redis_conn = await self._get_redis()
            acquired = await redis_conn.set(
                LOCK_KEY,
                f"worker:{os.getpid()}:{datetime.now(timezone.utc).isoformat()}",
                nx=True,  # Only set if not exists
                ex=LOCK_TTL_SECONDS
            )
            return bool(acquired)
        except Exception as e:
            logger.error(f"MeteringWorker: Failed to acquire lock: {e}")
            return False

    async def _release_lock(self):
        """Release distributed lock"""
        try:
            redis_conn = await self._get_redis()
            await redis_conn.delete(LOCK_KEY)
        except Exception as e:
            logger.warning(f"MeteringWorker: Failed to release lock: {e}")

    async def _extend_lock(self):
        """Extend lock TTL during long-running processing"""
        try:
            redis_conn = await self._get_redis()
            await redis_conn.expire(LOCK_KEY, LOCK_TTL_SECONDS)
        except Exception:
            pass

    async def _update_health(self, status: str, events_processed: int = 0):
        """Update health metrics in Redis"""
        try:
            redis_conn = await self._get_redis()
            now = datetime.now(timezone.utc).isoformat()

            await redis_conn.hset(HEALTH_KEY, mapping={
                "status": status,
                "last_run": now,
                "events_processed": events_processed,
                "worker_pid": os.getpid()
            })
            await redis_conn.expire(HEALTH_KEY, LOCK_TTL_SECONDS * 2)

            await redis_conn.set(LAST_RUN_KEY, now)
            await redis_conn.expire(LAST_RUN_KEY, LOCK_TTL_SECONDS * 2)

        except Exception as e:
            logger.warning(f"MeteringWorker: Failed to update health: {e}")

    async def _process_batch(self) -> int:
        """
        Process a batch of usage events.

        Returns number of events processed.
        """
        from database import SessionLocal
        from services.metering_service import get_metering_service

        db = SessionLocal()
        try:
            metering = get_metering_service()
            events_processed = await metering.process_batch(db, BATCH_SIZE)
            return events_processed
        finally:
            db.close()

    async def _run_cycle(self):
        """Run one processing cycle"""
        cycle_start = datetime.now(timezone.utc)

        # Try to acquire lock
        if not await self._acquire_lock():
            logger.debug("MeteringWorker: Another instance is processing, skipping")
            return

        try:
            logger.info("MeteringWorker: Starting processing cycle")
            await self._update_health("processing")

            total_processed = 0
            batch_count = 0

            # Process batches until queue is empty
            while True:
                # Extend lock for long-running processing
                await self._extend_lock()

                events = await self._process_batch()
                if events == 0:
                    break

                total_processed += events
                batch_count += 1

                # Log progress
                if batch_count % 10 == 0:
                    logger.info(
                        f"MeteringWorker: Processed {total_processed} events "
                        f"({batch_count} batches)"
                    )

            cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()

            logger.info(
                f"MeteringWorker: Cycle complete - "
                f"processed {total_processed} events in {cycle_duration:.2f}s"
            )

            await self._update_health("idle", total_processed)

        except Exception as e:
            logger.error(f"MeteringWorker: Processing cycle failed: {e}")
            await self._update_health("error")
            raise

        finally:
            await self._release_lock()

    async def _worker_loop(self):
        """Main worker loop"""
        logger.info(
            f"MeteringWorker: Starting with interval={WORKER_INTERVAL_SECONDS}s, "
            f"batch_size={BATCH_SIZE}"
        )

        while self._running:
            try:
                await self._run_cycle()
            except Exception as e:
                logger.error(f"MeteringWorker: Error in cycle: {e}")

            # Wait for next interval or shutdown
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=WORKER_INTERVAL_SECONDS
                )
                # Shutdown event was set
                break
            except asyncio.TimeoutError:
                # Normal timeout, continue to next cycle
                continue

        logger.info("MeteringWorker: Stopped")

    async def start(self):
        """Start the worker"""
        if self._running:
            return

        self._running = True
        self._shutdown_event.clear()
        self._task = asyncio.create_task(self._worker_loop())

    async def stop(self):
        """Stop the worker gracefully"""
        if not self._running:
            return

        logger.info("MeteringWorker: Stopping...")
        self._running = False
        self._shutdown_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=30)
            except asyncio.TimeoutError:
                logger.warning("MeteringWorker: Force stopping")
                self._task.cancel()

        if self._redis:
            await self._redis.close()
            self._redis = None

    async def run_once(self):
        """Run a single processing cycle (for testing)"""
        try:
            await self._run_cycle()
        except Exception as e:
            logger.error(f"MeteringWorker: Single run failed: {e}")
            raise

    async def get_health(self) -> dict:
        """Get worker health status"""
        try:
            redis_conn = await self._get_redis()
            health = await redis_conn.hgetall(HEALTH_KEY)
            return health if health else {"status": "unknown"}
        except Exception:
            return {"status": "error"}


# =============================================================================
# STANDALONE RUNNER
# =============================================================================

async def run_worker():
    """Run worker as standalone process"""
    worker = MeteringWorker()

    # Handle shutdown signals
    loop = asyncio.get_event_loop()

    def signal_handler():
        asyncio.create_task(worker.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    await worker.start()

    # Wait for worker to complete
    if worker._task:
        await worker._task


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(run_worker())
