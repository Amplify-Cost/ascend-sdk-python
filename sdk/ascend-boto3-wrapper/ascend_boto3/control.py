"""
SEC-103/104/105: Agent Control Module - Real-time Kill-Switch via SQS

Provides real-time agent control through SQS polling.
Enables immediate response to BLOCK/UNBLOCK commands from ASCEND platform.

Architecture:
    ASCEND Platform                SQS Queue                   SDK Agent
    ┌─────────────┐    ┌─────────────────────────┐    ┌─────────────────────┐
    │ Admin sends │───▶│ ascend-agent-control-   │◀───│ AgentControlClient  │
    │ BLOCK cmd   │    │ org-{org_id}            │    │ polls every 5s      │
    └─────────────┘    │ (long-poll: 20s wait)   │    │                     │
                       └─────────────────────────┘    │ On BLOCK:           │
                                                      │ - Set blocked=True  │
                                                      │ - Stop all ops      │
                                                      └─────────────────────┘

Target Latency: < 500ms from command issue to agent stop

Usage:
    from ascend_boto3.control import AgentControlClient

    # Initialize with organization queue URL
    control = AgentControlClient(
        queue_url="https://sqs.us-east-2.amazonaws.com/110948415588/ascend-agent-control-org-34",
        agent_id="boto3-agent-001"
    )

    # Start background polling (non-blocking)
    control.start_polling()

    # Check if agent is blocked before operations
    if control.is_blocked():
        raise RuntimeError("Agent is blocked by administrator")

    # Manual check for new commands
    control.check_commands()

    # Stop polling on shutdown
    control.stop_polling()

Compliance:
- SOC 2 CC6.2: Logical access controls
- NIST IR-4: Incident handling
- HIPAA 164.308(a)(6): Security incident procedures

Authored-By: ASCEND Engineering Team
"""
import boto3
import json
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

# Default polling configuration
DEFAULT_POLL_INTERVAL = 5  # seconds between polls
DEFAULT_WAIT_TIME = 20     # SQS long-poll wait time (max 20s)
DEFAULT_VISIBILITY_TIMEOUT = 30  # seconds message is hidden after receive


class AgentControlClient:
    """
    Real-time agent control via SQS polling.

    Polls organization-specific SQS queue for control commands (BLOCK, UNBLOCK, etc.)
    and maintains agent state accordingly.

    Thread-safe for use with background polling.
    """

    def __init__(
        self,
        queue_url: str,
        agent_id: str,
        region: str = "us-east-2",
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        on_block: Optional[Callable[[Dict], None]] = None,
        on_unblock: Optional[Callable[[Dict], None]] = None,
        on_command: Optional[Callable[[Dict], None]] = None
    ):
        """
        Initialize the control client.

        Args:
            queue_url: SQS queue URL (e.g., https://sqs.us-east-2.amazonaws.com/.../ascend-agent-control-org-34)
            agent_id: Unique identifier for this agent
            region: AWS region
            poll_interval: Seconds between poll attempts (default: 5)
            on_block: Callback when BLOCK command received
            on_unblock: Callback when UNBLOCK command received
            on_command: Callback for any command (receives full command dict)
        """
        self.queue_url = queue_url
        self.agent_id = agent_id
        self.region = region
        self.poll_interval = poll_interval
        self.sqs_client = boto3.client('sqs', region_name=region)

        # Callbacks
        self.on_block = on_block
        self.on_unblock = on_unblock
        self.on_command = on_command

        # State
        self._blocked = False
        self._block_reason = None
        self._block_command_id = None
        self._last_command = None
        self._lock = threading.Lock()

        # Background polling
        self._polling = False
        self._poll_thread = None
        self._stop_event = threading.Event()

        # Metrics
        self._commands_received = 0
        self._poll_errors = 0
        self._last_poll_time = None

    @property
    def is_blocked(self) -> bool:
        """Check if agent is currently blocked."""
        with self._lock:
            return self._blocked

    @property
    def block_reason(self) -> Optional[str]:
        """Get the reason for current block (if blocked)."""
        with self._lock:
            return self._block_reason

    @property
    def stats(self) -> Dict[str, Any]:
        """Get polling statistics."""
        with self._lock:
            return {
                "blocked": self._blocked,
                "block_reason": self._block_reason,
                "commands_received": self._commands_received,
                "poll_errors": self._poll_errors,
                "last_poll_time": self._last_poll_time,
                "polling_active": self._polling
            }

    def check_commands(self) -> list:
        """
        Manually check for control commands (synchronous).

        Returns:
            List of commands received (may be empty)
        """
        commands = []

        try:
            # Long-poll SQS with 20 second wait
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=DEFAULT_WAIT_TIME,
                VisibilityTimeout=DEFAULT_VISIBILITY_TIMEOUT,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )

            messages = response.get('Messages', [])
            self._last_poll_time = datetime.utcnow().isoformat()

            for message in messages:
                try:
                    command = self._process_message(message)
                    if command:
                        commands.append(command)
                except Exception as e:
                    logger.error(f"SEC-103: Failed to process message: {e}")

        except Exception as e:
            self._poll_errors += 1
            logger.error(f"SEC-103: SQS poll failed: {e}")

        return commands

    def _process_message(self, message: dict) -> Optional[dict]:
        """Process a single SQS message."""
        body = message.get('Body', '{}')
        receipt_handle = message.get('ReceiptHandle')

        try:
            command = json.loads(body)
        except json.JSONDecodeError:
            logger.warning(f"SEC-103: Invalid JSON in message: {body[:100]}")
            # Delete invalid message
            self._delete_message(receipt_handle)
            return None

        # Check if command is for this agent or broadcast
        target_agent = command.get('agent_id')
        if target_agent and target_agent != self.agent_id:
            # Command is for different agent, skip but don't delete
            # (other agents in org may need it)
            return None

        command_type = command.get('command_type', 'UNKNOWN')
        command_id = command.get('command_id')
        reason = command.get('reason', 'No reason provided')

        logger.info(f"SEC-103: Received {command_type} command (id={command_id})")

        # Update agent state based on command type
        with self._lock:
            self._commands_received += 1
            self._last_command = command

            if command_type == 'BLOCK':
                self._blocked = True
                self._block_reason = reason
                self._block_command_id = command_id
                logger.warning(f"SEC-103: AGENT BLOCKED - {reason}")
                if self.on_block:
                    try:
                        self.on_block(command)
                    except Exception as e:
                        logger.error(f"SEC-103: on_block callback failed: {e}")

            elif command_type == 'UNBLOCK':
                self._blocked = False
                self._block_reason = None
                self._block_command_id = None
                logger.info(f"SEC-103: Agent unblocked - {reason}")
                if self.on_unblock:
                    try:
                        self.on_unblock(command)
                    except Exception as e:
                        logger.error(f"SEC-103: on_unblock callback failed: {e}")

            elif command_type in ('SUSPEND', 'QUARANTINE'):
                # Treat like BLOCK
                self._blocked = True
                self._block_reason = f"{command_type}: {reason}"
                self._block_command_id = command_id

            elif command_type == 'RESUME':
                # Treat like UNBLOCK
                self._blocked = False
                self._block_reason = None
                self._block_command_id = None

        # General callback
        if self.on_command:
            try:
                self.on_command(command)
            except Exception as e:
                logger.error(f"SEC-103: on_command callback failed: {e}")

        # Delete processed message
        self._delete_message(receipt_handle)

        return command

    def _delete_message(self, receipt_handle: str):
        """Delete a processed message from SQS."""
        if receipt_handle:
            try:
                self.sqs_client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
            except Exception as e:
                logger.error(f"SEC-103: Failed to delete message: {e}")

    def start_polling(self):
        """Start background polling thread."""
        if self._polling:
            logger.warning("SEC-103: Polling already active")
            return

        self._polling = True
        self._stop_event.clear()
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            name="ascend-control-poller",
            daemon=True
        )
        self._poll_thread.start()
        logger.info(f"SEC-103: Started control polling (interval={self.poll_interval}s)")

    def stop_polling(self, timeout: float = 30.0):
        """
        Stop background polling thread.

        Args:
            timeout: Seconds to wait for thread to stop
        """
        if not self._polling:
            return

        self._stop_event.set()
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=timeout)

        self._polling = False
        logger.info("SEC-103: Stopped control polling")

    def _poll_loop(self):
        """Background polling loop."""
        while not self._stop_event.is_set():
            try:
                # Check for commands (blocking for up to WAIT_TIME seconds)
                self.check_commands()
            except Exception as e:
                logger.error(f"SEC-103: Poll loop error: {e}")

            # Sleep between polls (but check stop_event frequently)
            self._stop_event.wait(timeout=self.poll_interval)

    def assert_not_blocked(self):
        """
        Raise an exception if agent is blocked.

        Call this before performing any operation.

        Raises:
            RuntimeError: If agent is blocked
        """
        if self.is_blocked:
            raise RuntimeError(
                f"Agent {self.agent_id} is blocked by administrator. "
                f"Reason: {self.block_reason}"
            )


def create_control_client(
    organization_id: int,
    agent_id: str,
    region: str = "us-east-2",
    account_id: str = "110948415588",
    **kwargs
) -> AgentControlClient:
    """
    Convenience factory to create AgentControlClient with standard queue URL.

    Args:
        organization_id: Organization ID (used in queue name)
        agent_id: Unique agent identifier
        region: AWS region
        account_id: AWS account ID
        **kwargs: Additional arguments for AgentControlClient

    Returns:
        Configured AgentControlClient instance
    """
    queue_url = f"https://sqs.{region}.amazonaws.com/{account_id}/ascend-agent-control-org-{organization_id}"
    return AgentControlClient(
        queue_url=queue_url,
        agent_id=agent_id,
        region=region,
        **kwargs
    )
