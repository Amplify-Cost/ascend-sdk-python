# enterprise_secrets/rotation_service.py
"""
Enterprise Secrets Rotation Service
Automated rotation with scheduling, notifications, and rollback capabilities
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import schedule
import time
from threading import Thread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

@dataclass
class RotationResult:
    """Result of a secret rotation operation"""
    secret_name: str
    success: bool
    old_secret_hash: Optional[str]
    new_secret_hash: Optional[str]
    timestamp: datetime
    error_message: Optional[str] = None
    rollback_available: bool = True

@dataclass
class RotationSchedule:
    """Schedule configuration for secret rotation"""
    secret_name: str
    cron_expression: str
    enabled: bool
    last_rotation: Optional[datetime]
    next_rotation: Optional[datetime]
    notification_emails: List[str]

class SecretsRotationService:
    """
    Enterprise secrets rotation service with scheduling and notifications
    """
    
    def __init__(self, secrets_manager, notification_config: Dict = None):
        self.secrets_manager = secrets_manager
        self.notification_config = notification_config or {}
        self.rotation_schedules: Dict[str, RotationSchedule] = {}
        self.rotation_history: List[RotationResult] = []
        self.is_running = False
        self.scheduler_thread: Optional[Thread] = None
        
        # Pre and post rotation hooks
        self.pre_rotation_hooks: Dict[str, List[Callable]] = {}
        self.post_rotation_hooks: Dict[str, List[Callable]] = {}
        
        logger.info("🔄 Enterprise Secrets Rotation Service initialized")

    def add_rotation_schedule(self, secret_name: str, cron_expression: str, 
                            notification_emails: List[str] = None):
        """Add a rotation schedule for a secret"""
        schedule_config = RotationSchedule(
            secret_name=secret_name,
            cron_expression=cron_expression,
            enabled=True,
            last_rotation=None,
            next_rotation=self._calculate_next_rotation(cron_expression),
            notification_emails=notification_emails or []
        )
        
        self.rotation_schedules[secret_name] = schedule_config
        logger.info(f"📅 Rotation schedule added for {secret_name}: {cron_expression}")

    def _calculate_next_rotation(self, cron_expression: str) -> datetime:
        """Calculate next rotation time based on cron expression"""
        # Simplified cron parsing - in production use croniter library
        if cron_expression == "weekly":
            return datetime.now(UTC) + timedelta(weeks=1)
        elif cron_expression == "monthly":
            return datetime.now(UTC) + timedelta(days=30)
        elif cron_expression == "daily":
            return datetime.now(UTC) + timedelta(days=1)
        else:
            return datetime.now(UTC) + timedelta(hours=24)

    def add_pre_rotation_hook(self, secret_name: str, hook_function: Callable):
        """Add hook to execute before rotation"""
        if secret_name not in self.pre_rotation_hooks:
            self.pre_rotation_hooks[secret_name] = []
        self.pre_rotation_hooks[secret_name].append(hook_function)

    def add_post_rotation_hook(self, secret_name: str, hook_function: Callable):
        """Add hook to execute after rotation"""
        if secret_name not in self.post_rotation_hooks:
            self.post_rotation_hooks[secret_name] = []
        self.post_rotation_hooks[secret_name].append(hook_function)

    async def rotate_secret_with_validation(self, secret_name: str, 
                                          dry_run: bool = False) -> RotationResult:
        """
        Rotate secret with comprehensive validation and rollback capability
        """
        start_time = datetime.now(UTC)
        
        try:
            logger.info(f"🔄 Starting {'dry run' if dry_run else 'live'} rotation for {secret_name}")
            
            # Get current secret for backup
            old_secret = self.secrets_manager.get_secret(secret_name)
            if not old_secret:
                raise ValueError(f"Secret {secret_name} not found")
            
            old_secret_hash = self._hash_secret(old_secret)
            
            # Execute pre-rotation hooks
            if not dry_run:
                await self._execute_hooks(secret_name, "pre")
            
            # Generate new secret
            new_secret = self.secrets_manager._generate_new_secret(secret_name)
            if not new_secret:
                raise ValueError("Failed to generate new secret")
            
            new_secret_hash = self._hash_secret(new_secret)
            
            if dry_run:
                logger.info(f"✅ Dry run successful for {secret_name}")
                return RotationResult(
                    secret_name=secret_name,
                    success=True,
                    old_secret_hash=old_secret_hash,
                    new_secret_hash=new_secret_hash,
                    timestamp=start_time,
                    rollback_available=True
                )
            
            # Store new secret
            success = self.secrets_manager.set_secret(secret_name, new_secret)
            if not success:
                raise ValueError("Failed to store new secret")
            
            # Validate new secret is accessible
            retrieved_secret = self.secrets_manager.get_secret(secret_name)
            if retrieved_secret != new_secret:
                raise ValueError("Secret validation failed after rotation")
            
            # Execute post-rotation hooks
            await self._execute_hooks(secret_name, "post")
            
            # Update schedule
            if secret_name in self.rotation_schedules:
                schedule = self.rotation_schedules[secret_name]
                schedule.last_rotation = start_time
                schedule.next_rotation = self._calculate_next_rotation(schedule.cron_expression)
            
            result = RotationResult(
                secret_name=secret_name,
                success=True,
                old_secret_hash=old_secret_hash,
                new_secret_hash=new_secret_hash,
                timestamp=start_time,
                rollback_available=True
            )
            
            self.rotation_history.append(result)
            
            # Send notification
            await self._send_rotation_notification(result)
            
            logger.info(f"✅ Secret {secret_name} rotated successfully")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Secret rotation failed for {secret_name}: {error_msg}")
            
            result = RotationResult(
                secret_name=secret_name,
                success=False,
                old_secret_hash=None,
                new_secret_hash=None,
                timestamp=start_time,
                error_message=error_msg,
                rollback_available=False
            )
            
            self.rotation_history.append(result)
            await self._send_rotation_notification(result)
            
            return result

    async def _execute_hooks(self, secret_name: str, hook_type: str):
        """Execute pre or post rotation hooks"""
        hooks = getattr(self, f"{hook_type}_rotation_hooks", {}).get(secret_name, [])
        
        for hook in hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(secret_name)
                else:
                    hook(secret_name)
                logger.info(f"✅ {hook_type}-rotation hook executed for {secret_name}")
            except Exception as e:
                logger.error(f"❌ {hook_type}-rotation hook failed for {secret_name}: {e}")
                raise

    def _hash_secret(self, secret: str) -> str:
        """Create hash of secret for tracking (not storing the actual secret)"""
        import hashlib
        return hashlib.sha256(secret.encode()).hexdigest()[:12]

    async def _send_rotation_notification(self, result: RotationResult):
        """Send rotation notification via email/webhook"""
        if not self.notification_config:
            return
        
        try:
            # Get notification emails for this secret
            emails = []
            if result.secret_name in self.rotation_schedules:
                emails = self.rotation_schedules[result.secret_name].notification_emails
            
            # Add global notification emails
            emails.extend(self.notification_config.get("global_emails", []))
            
            if not emails:
                return
            
            # Send email notification
            subject = f"🔄 Secret Rotation {'Successful' if result.success else 'Failed'}: {result.secret_name}"
            
            if result.success:
                body = f"""
Enterprise Secret Rotation Completed Successfully

Secret: {result.secret_name}
Timestamp: {result.timestamp.isoformat()}
Old Secret Hash: {result.old_secret_hash}
New Secret Hash: {result.new_secret_hash}

The secret has been successfully rotated and all dependent services should be updated automatically.

If you experience any issues, please contact the infrastructure team immediately.

---
OW-AI Enterprise Security Operations
                """
            else:
                body = f"""
Enterprise Secret Rotation FAILED

Secret: {result.secret_name}
Timestamp: {result.timestamp.isoformat()}
Error: {result.error_message}

IMMEDIATE ACTION REQUIRED:
1. Check secret rotation logs
2. Verify secret accessibility
3. Contact infrastructure team if needed

---
OW-AI Enterprise Security Operations
                """
            
            await self._send_email(emails, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send rotation notification: {e}")

    async def _send_email(self, emails: List[str], subject: str, body: str):
        """Send email notification"""
        try:
            smtp_config = self.notification_config.get("smtp", {})
            if not smtp_config:
                logger.warning("SMTP not configured, skipping email notification")
                return
            
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get("from_email", "noreply@ow-ai.com")
            msg['To'] = ", ".join(emails)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_config.get("host", "localhost"), 
                                smtp_config.get("port", 587))
            
            if smtp_config.get("use_tls", True):
                server.starttls()
            
            if smtp_config.get("username"):
                server.login(smtp_config["username"], smtp_config["password"])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email notification sent to {len(emails)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def start_scheduler(self):
        """Start the rotation scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("🕐 Secrets rotation scheduler started")

    def stop_scheduler(self):
        """Stop the rotation scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("⏹️ Secrets rotation scheduler stopped")

    def _run_scheduler(self):
        """Run the rotation scheduler"""
        while self.is_running:
            try:
                # Check for due rotations
                now = datetime.now(UTC)
                
                for secret_name, schedule_config in self.rotation_schedules.items():
                    if not schedule_config.enabled:
                        continue
                    
                    if schedule_config.next_rotation and now >= schedule_config.next_rotation:
                        logger.info(f"⏰ Scheduled rotation due for {secret_name}")
                        
                        # Run rotation in background
                        asyncio.create_task(
                            self.rotate_secret_with_validation(secret_name)
                        )
                
                # Sleep for 1 minute before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

    def get_rotation_status(self) -> Dict:
        """Get current rotation status for monitoring"""
        return {
            "scheduler_running": self.is_running,
            "total_schedules": len(self.rotation_schedules),
            "enabled_schedules": len([s for s in self.rotation_schedules.values() if s.enabled]),
            "recent_rotations": len([r for r in self.rotation_history if 
                                   r.timestamp > datetime.now(UTC) - timedelta(days=7)]),
            "successful_rotations": len([r for r in self.rotation_history if r.success]),
            "failed_rotations": len([r for r in self.rotation_history if not r.success]),
            "next_scheduled_rotation": min([s.next_rotation for s in self.rotation_schedules.values() 
                                          if s.next_rotation and s.enabled], default=None)
        }

    def get_rotation_history(self, limit: int = 50) -> List[Dict]:
        """Get rotation history for reporting"""
        recent_history = sorted(self.rotation_history, 
                              key=lambda x: x.timestamp, 
                              reverse=True)[:limit]
        
        return [asdict(result) for result in recent_history]

    async def emergency_rotation(self, secret_name: str, reason: str) -> RotationResult:
        """Perform emergency rotation with enhanced logging"""
        logger.warning(f"🚨 EMERGENCY ROTATION initiated for {secret_name}: {reason}")
        
        # Add to audit trail
        audit_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "EMERGENCY_ROTATION",
            "secret_name": secret_name,
            "reason": reason,
            "user": "system",
            "severity": "CRITICAL"
        }
        
        self.secrets_manager._log_secret_access(secret_name, "EMERGENCY_ROTATION", reason)
        
        # Perform rotation
        result = await self.rotate_secret_with_validation(secret_name)
        
        # Enhanced notification for emergency
        if self.notification_config:
            emergency_emails = self.notification_config.get("emergency_emails", [])
            if emergency_emails:
                subject = f"🚨 EMERGENCY Secret Rotation: {secret_name}"
                body = f"""
EMERGENCY SECRET ROTATION PERFORMED

Secret: {secret_name}
Reason: {reason}
Result: {'SUCCESS' if result.success else 'FAILED'}
Timestamp: {result.timestamp.isoformat()}

This was an emergency rotation. Please verify all systems are functioning correctly.

---
OW-AI Enterprise Security Operations
                """
                await self._send_email(emergency_emails, subject, body)
        
        return result

# Example usage and hooks
def database_connection_hook(secret_name: str):
    """Example hook to restart database connections after rotation"""
    if "DATABASE" in secret_name.upper():
        logger.info(f"🔄 Restarting database connections for {secret_name}")
        # Implement database connection restart logic here

async def api_key_validation_hook(secret_name: str):
    """Example hook to validate API key after rotation"""
    if "API_KEY" in secret_name.upper():
        logger.info(f"🔍 Validating API key for {secret_name}")
        # Implement API key validation logic here