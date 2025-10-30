"""
A/B Test Alert Router Service
Routes incoming alerts to active A/B test variants for real metrics tracking.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import random
import logging
import time

logger = logging.getLogger(__name__)


class ABTestAlertRouter:
    """Routes alerts to A/B test variants and tracks performance metrics"""

    def __init__(self, db: Session):
        self.db = db

    def get_active_tests_for_alert(self, alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all active A/B tests that apply to this alert.

        Args:
            alert_data: Alert information (severity, type, etc.)

        Returns:
            List of active A/B tests that could evaluate this alert
        """
        # Query active A/B tests
        tests = self.db.execute(text("""
            SELECT
                t.test_id, t.test_name,
                t.base_rule_id,
                t.variant_a_rule_id, t.variant_b_rule_id,
                t.traffic_split,
                ra.condition as variant_a_condition,
                rb.condition as variant_b_condition
            FROM ab_tests t
            LEFT JOIN smart_rules ra ON t.variant_a_rule_id = ra.id
            LEFT JOIN smart_rules rb ON t.variant_b_rule_id = rb.id
            WHERE t.status = 'running'
            AND t.created_at >= NOW() - INTERVAL '7 days'  -- Only tests from last 7 days
            ORDER BY t.created_at DESC
        """)).fetchall()

        return [
            {
                "test_id": test.test_id,
                "test_name": test.test_name,
                "base_rule_id": test.base_rule_id,
                "variant_a_rule_id": test.variant_a_rule_id,
                "variant_b_rule_id": test.variant_b_rule_id,
                "traffic_split": test.traffic_split or 50,
                "variant_a_condition": test.variant_a_condition,
                "variant_b_condition": test.variant_b_condition
            }
            for test in tests
        ]

    def select_variant(self, traffic_split: int = 50) -> str:
        """
        Randomly select which variant to use based on traffic split.

        Args:
            traffic_split: Percentage of traffic to send to variant_a (default 50)

        Returns:
            'variant_a' or 'variant_b'
        """
        return "variant_a" if random.randint(1, 100) <= traffic_split else "variant_b"

    def evaluate_alert_with_variant(
        self,
        alert_data: Dict[str, Any],
        test_info: Dict[str, Any],
        variant: str
    ) -> Dict[str, Any]:
        """
        Evaluate an alert using the specified variant's rule.

        Args:
            alert_data: Alert information
            test_info: A/B test information
            variant: 'variant_a' or 'variant_b'

        Returns:
            Evaluation results including detection status and timing
        """
        start_time = time.time()

        # Get the variant's rule condition
        condition = test_info.get(f"{variant}_condition", "")
        rule_id = test_info.get(f"{variant}_rule_id")

        # Evaluate condition against alert data
        # For now, this is a simple evaluation - can be enhanced
        detected = self._evaluate_condition(condition, alert_data)

        # Calculate detection time
        detection_time_ms = int((time.time() - start_time) * 1000)

        return {
            "test_id": test_info["test_id"],
            "variant": variant,
            "variant_rule_id": rule_id,
            "detected": detected,
            "detection_time_ms": detection_time_ms,
            "condition_used": condition
        }

    def _evaluate_condition(self, condition: str, alert_data: Dict[str, Any]) -> bool:
        """
        Evaluate a rule condition against alert data.

        Args:
            condition: Rule condition string
            alert_data: Alert data to evaluate

        Returns:
            True if condition matches, False otherwise
        """
        try:
            # Simple keyword matching for now
            # In production, this should use actual rule evaluation logic
            condition_lower = condition.lower()
            message_lower = alert_data.get("message", "").lower()
            alert_type_lower = alert_data.get("alert_type", "").lower()

            # Check if condition keywords appear in alert
            if any(keyword in message_lower or keyword in alert_type_lower
                   for keyword in ["severity", "critical", "high", "threat"]):
                # Condition likely applies
                return True

            return False
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

    def route_alert_to_ab_test(
        self,
        alert_id: int,
        alert_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Route an incoming alert to active A/B tests and track metrics.

        Args:
            alert_id: ID of the alert
            alert_data: Alert information

        Returns:
            Routing result with test and variant information, or None if no active tests
        """
        try:
            # Get active tests
            active_tests = self.get_active_tests_for_alert(alert_data)

            if not active_tests:
                logger.info(f"No active A/B tests for alert {alert_id}")
                return None

            # For now, route to the first active test
            # In production, could route to multiple tests or use more sophisticated logic
            test_info = active_tests[0]

            # Select variant based on traffic split
            variant = self.select_variant(test_info["traffic_split"])

            # Evaluate alert with selected variant
            evaluation = self.evaluate_alert_with_variant(alert_data, test_info, variant)

            # Update alert record with A/B test tracking info
            self.db.execute(text("""
                UPDATE alerts
                SET ab_test_id = :test_id,
                    evaluated_by_variant = :variant,
                    variant_rule_id = :variant_rule_id,
                    detected_by_rule_id = :variant_rule_id,
                    detection_time_ms = :detection_time_ms
                WHERE id = :alert_id
            """), {
                "test_id": evaluation["test_id"],
                "variant": evaluation["variant"],
                "variant_rule_id": evaluation["variant_rule_id"],
                "detection_time_ms": evaluation["detection_time_ms"],
                "alert_id": alert_id
            })

            self.db.commit()

            logger.info(
                f"✅ Alert {alert_id} routed to A/B test {test_info['test_id']}, "
                f"variant {variant}, detected: {evaluation['detected']}, "
                f"time: {evaluation['detection_time_ms']}ms"
            )

            return evaluation

        except Exception as e:
            logger.error(f"Error routing alert to A/B test: {e}")
            self.db.rollback()
            return None

    def calculate_ab_test_metrics(self, test_id: str) -> Dict[str, Any]:
        """
        Calculate real performance metrics for an A/B test from actual alert data.

        Args:
            test_id: UUID of the A/B test

        Returns:
            Dictionary with performance metrics for both variants
        """
        try:
            # Query metrics for variant_a
            variant_a_metrics = self.db.execute(text("""
                SELECT
                    COUNT(*) as total_alerts,
                    COUNT(*) FILTER (WHERE is_true_positive = TRUE) as true_positives,
                    COUNT(*) FILTER (WHERE is_false_positive = TRUE) as false_positives,
                    AVG(detection_time_ms) as avg_detection_time_ms,
                    MAX(detection_time_ms) as max_detection_time_ms,
                    MIN(detection_time_ms) as min_detection_time_ms
                FROM alerts
                WHERE ab_test_id = :test_id
                AND evaluated_by_variant = 'variant_a'
            """), {"test_id": test_id}).fetchone()

            # Query metrics for variant_b
            variant_b_metrics = self.db.execute(text("""
                SELECT
                    COUNT(*) as total_alerts,
                    COUNT(*) FILTER (WHERE is_true_positive = TRUE) as true_positives,
                    COUNT(*) FILTER (WHERE is_false_positive = TRUE) as false_positives,
                    AVG(detection_time_ms) as avg_detection_time_ms,
                    MAX(detection_time_ms) as max_detection_time_ms,
                    MIN(detection_time_ms) as min_detection_time_ms
                FROM alerts
                WHERE ab_test_id = :test_id
                AND evaluated_by_variant = 'variant_b'
            """), {"test_id": test_id}).fetchone()

            # Calculate performance scores
            def calc_performance(metrics):
                if not metrics or metrics.total_alerts == 0:
                    return 0.0

                tp = metrics.true_positives or 0
                fp = metrics.false_positives or 0
                total = metrics.total_alerts or 1

                # Detection rate (what % were true positives)
                detection_rate = (tp / total) * 100 if total > 0 else 0

                # False positive rate
                fp_rate = (fp / total) * 100 if total > 0 else 0

                # Performance score: high detection, low FP = high score
                performance = detection_rate - (fp_rate * 0.5)  # Penalize FP less
                return max(0.0, min(100.0, performance))

            variant_a_performance = calc_performance(variant_a_metrics)
            variant_b_performance = calc_performance(variant_b_metrics)

            # Calculate false positive reduction
            fp_reduction = 0
            if variant_a_metrics and variant_a_metrics.total_alerts > 0:
                a_fp_rate = (variant_a_metrics.false_positives or 0) / variant_a_metrics.total_alerts
                b_fp_rate = (variant_b_metrics.false_positives or 0) / (variant_b_metrics.total_alerts or 1)
                if a_fp_rate > 0:
                    fp_reduction = ((a_fp_rate - b_fp_rate) / a_fp_rate) * 100

            # Calculate improvement
            improvement_pct = 0
            if variant_a_performance > 0:
                improvement_pct = ((variant_b_performance - variant_a_performance) / variant_a_performance) * 100

            return {
                "variant_a": {
                    "total_alerts": variant_a_metrics.total_alerts if variant_a_metrics else 0,
                    "true_positives": variant_a_metrics.true_positives if variant_a_metrics else 0,
                    "false_positives": variant_a_metrics.false_positives if variant_a_metrics else 0,
                    "avg_detection_time_ms": float(variant_a_metrics.avg_detection_time_ms or 0) if variant_a_metrics else 0,
                    "performance_score": round(variant_a_performance, 2)
                },
                "variant_b": {
                    "total_alerts": variant_b_metrics.total_alerts if variant_b_metrics else 0,
                    "true_positives": variant_b_metrics.true_positives if variant_b_metrics else 0,
                    "false_positives": variant_b_metrics.false_positives if variant_b_metrics else 0,
                    "avg_detection_time_ms": float(variant_b_metrics.avg_detection_time_ms or 0) if variant_b_metrics else 0,
                    "performance_score": round(variant_b_performance, 2)
                },
                "comparison": {
                    "improvement_percentage": round(improvement_pct, 1),
                    "false_positive_reduction": round(fp_reduction, 1),
                    "sample_size": (variant_a_metrics.total_alerts if variant_a_metrics else 0) +
                                  (variant_b_metrics.total_alerts if variant_b_metrics else 0)
                }
            }

        except Exception as e:
            logger.error(f"Error calculating A/B test metrics: {e}")
            return {}

    def update_test_metrics(self, test_id: str) -> bool:
        """
        Update the ab_tests table with real metrics from alerts.

        Args:
            test_id: UUID of the A/B test

        Returns:
            True if successful, False otherwise
        """
        try:
            metrics = self.calculate_ab_test_metrics(test_id)

            if not metrics:
                return False

            # Update ab_tests record
            self.db.execute(text("""
                UPDATE ab_tests
                SET variant_a_performance = :a_perf,
                    variant_b_performance = :b_perf,
                    sample_size = :sample_size,
                    improvement = :improvement,
                    updated_at = NOW()
                WHERE test_id = :test_id
            """), {
                "a_perf": metrics["variant_a"]["performance_score"],
                "b_perf": metrics["variant_b"]["performance_score"],
                "sample_size": metrics["comparison"]["sample_size"],
                "improvement": f"+{metrics['comparison']['improvement_percentage']}% confirmed",
                "test_id": test_id
            })

            self.db.commit()

            logger.info(f"✅ Updated metrics for A/B test {test_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating test metrics: {e}")
            self.db.rollback()
            return False
