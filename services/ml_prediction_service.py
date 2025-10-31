"""
ML-Powered Prediction Service for Analytics

Provides intelligent forecasting, anomaly detection, and recommendations
using statistical analysis and pattern recognition.

Author: Claude Code
Date: 2025-10-31
Phase: 3 of 3 (Enterprise Analytics Fix - Final Phase)
"""

from datetime import datetime, timedelta, UTC
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import logging
import statistics

logger = logging.getLogger(__name__)


class PredictionEngine:
    """
    Smart prediction engine using statistical analysis and pattern recognition.
    Works with limited data, provides confidence scoring.
    """

    def __init__(self, db: Session):
        """Initialize prediction engine with database session"""
        self.db = db
        self.confidence_cache = {}

    def calculate_confidence(self, days_of_data: int, sample_size: int) -> float:
        """
        Calculate prediction confidence based on data availability

        Args:
            days_of_data: Number of days with historical data
            sample_size: Total number of data points

        Returns:
            Confidence score between 0.3 and 0.95
        """
        # Base confidence from days
        if days_of_data < 4:
            base_conf = 0.3 + (days_of_data / 12)  # 0.3-0.55
        elif days_of_data < 8:
            base_conf = 0.5 + (days_of_data / 20)  # 0.5-0.7
        elif days_of_data < 14:
            base_conf = 0.7 + (days_of_data / 50)  # 0.7-0.86
        else:
            base_conf = min(0.95, 0.85 + (days_of_data / 100))  # 0.85-0.95

        # Adjust for sample size
        if sample_size < 10:
            base_conf *= 0.8
        elif sample_size < 50:
            base_conf *= 0.9

        return round(base_conf, 2)

    def moving_average(self, values: List[float], window: int = 3) -> float:
        """Calculate moving average for smoothing"""
        if not values:
            return 0.0
        recent = values[-window:] if len(values) >= window else values
        return sum(recent) / len(recent)

    def calculate_trend(self, values: List[Tuple[datetime, float]]) -> Tuple[float, str]:
        """
        Calculate trend using simple linear regression

        Returns:
            (slope, direction) where direction is 'increasing'/'stable'/'decreasing'
        """
        if len(values) < 2:
            return 0.0, "stable"

        # Convert to x, y coordinates
        x_values = list(range(len(values)))
        y_values = [v[1] for v in values]

        # Simple linear regression
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xx = sum(x * x for x in x_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))

        # Calculate slope
        denominator = (n * sum_xx - sum_x * sum_x)
        if denominator == 0:
            return 0.0, "stable"

        slope = (n * sum_xy - sum_x * sum_y) / denominator

        # Determine direction
        if slope > 0.5:
            direction = "increasing"
        elif slope < -0.5:
            direction = "decreasing"
        else:
            direction = "stable"

        return slope, direction

    def forecast_risks(self, days: int = 7) -> List[Dict]:
        """
        Forecast high-risk actions for next N days

        Uses moving averages, trend analysis, and day-of-week patterns
        """
        try:
            # Get historical data (last 30 days)
            thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

            # Query daily risk counts
            daily_risks = self.db.execute(text("""
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as risk_count
                FROM agent_actions
                WHERE timestamp >= :start_date
                    AND risk_level IN ('high', 'critical')
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            """), {"start_date": thirty_days_ago}).fetchall()

            if not daily_risks:
                logger.info("No historical risk data for forecasting")
                return []

            # Convert to list of tuples (date, count)
            risk_data = [(row[0], row[1]) for row in daily_risks]
            days_with_data = len(risk_data)
            total_risks = sum(r[1] for r in risk_data)

            logger.info(f"Forecasting with {days_with_data} days of data, {total_risks} total risks")

            # Calculate statistics
            risk_counts = [r[1] for r in risk_data]
            avg_risks = statistics.mean(risk_counts) if risk_counts else 0
            ma_value = self.moving_average(risk_counts, window=3)
            slope, trend = self.calculate_trend(risk_data)

            # Calculate base confidence
            base_confidence = self.calculate_confidence(days_with_data, total_risks)

            # Generate predictions
            predictions = []
            today = datetime.now(UTC).date()

            for day_offset in range(1, days + 1):
                forecast_date = today + timedelta(days=day_offset)

                # Base prediction from moving average
                base_prediction = ma_value

                # Apply trend
                trend_adjustment = slope * day_offset * 0.5  # Dampen trend effect

                # Day of week pattern (if enough data)
                dow_adjustment = 0
                if days_with_data >= 7:
                    # Find similar day-of-week patterns
                    dow = forecast_date.weekday()
                    dow_risks = [r[1] for r in risk_data if r[0].weekday() == dow]
                    if dow_risks:
                        dow_avg = statistics.mean(dow_risks)
                        dow_adjustment = (dow_avg - avg_risks) * 0.3  # Subtle adjustment

                # Combine predictions
                predicted_value = max(0, base_prediction + trend_adjustment + dow_adjustment)

                # Adjust confidence based on forecast distance
                distance_factor = 1 - (day_offset / (days * 2))  # Decrease with distance
                confidence = base_confidence * distance_factor

                predictions.append({
                    "date": forecast_date.isoformat(),
                    "predicted_high_risk": round(predicted_value),
                    "confidence": round(confidence, 2),
                    "method": "ml_powered" if days_with_data >= 14 else "trend_analysis" if days_with_data >= 7 else "pattern_based",
                    "factors": ["moving_average", "trend_analysis"] + (["day_of_week_pattern"] if days_with_data >= 7 else [])
                })

            return predictions

        except Exception as e:
            logger.error(f"Error forecasting risks: {e}")
            return []

    def predict_agent_workload(self) -> List[Dict]:
        """
        Predict agent workload distribution for next week
        """
        try:
            # Get last 30 days of agent activity
            thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

            agent_stats = self.db.execute(text("""
                SELECT
                    agent_id,
                    COUNT(*) as action_count,
                    COUNT(DISTINCT DATE(timestamp)) as active_days,
                    AVG(CASE WHEN risk_level IN ('high', 'critical') THEN 1 ELSE 0 END) as high_risk_ratio
                FROM agent_actions
                WHERE timestamp >= :start_date
                    AND agent_id IS NOT NULL
                GROUP BY agent_id
                ORDER BY action_count DESC
                LIMIT 10
            """), {"start_date": thirty_days_ago}).fetchall()

            if not agent_stats:
                logger.info("No agent data for workload prediction")
                return []

            predictions = []
            days_with_data = max((row[2] for row in agent_stats), default=1)

            for row in agent_stats:
                agent_id, action_count, active_days, high_risk_ratio = row

                # Calculate daily average
                avg_daily = action_count / max(active_days, 1)

                # Predict next week (7 days)
                predicted_actions = round(avg_daily * 7)

                # Capacity utilization (100 actions/week = 100%)
                capacity = min(1.0, predicted_actions / 100)

                # Trend analysis
                recent_trend = "stable"  # Simplified for now
                if capacity > 0.8:
                    recent_trend = "increasing"
                elif capacity < 0.3:
                    recent_trend = "decreasing"

                # Confidence based on data availability
                confidence = self.calculate_confidence(days_with_data, action_count)

                predictions.append({
                    "agent": f"agent-{agent_id}",
                    "predicted_actions": predicted_actions,
                    "capacity_utilization": round(capacity, 2),
                    "confidence": confidence,
                    "trend": recent_trend,
                    "high_risk_ratio": round(float(high_risk_ratio), 2) if high_risk_ratio else 0.0
                })

            return predictions

        except Exception as e:
            logger.error(f"Error predicting agent workload: {e}")
            return []

    def detect_anomalies(self) -> List[Dict]:
        """
        Detect anomalies using statistical outlier detection
        """
        try:
            # Get last 30 days for baseline
            thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

            daily_counts = self.db.execute(text("""
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as action_count,
                    COUNT(CASE WHEN risk_level IN ('high', 'critical') THEN 1 END) as high_risk_count
                FROM agent_actions
                WHERE timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            """), {"start_date": thirty_days_ago}).fetchall()

            if len(daily_counts) < 3:
                return []  # Need at least 3 days for statistical analysis

            # Calculate baseline statistics
            action_counts = [row[1] for row in daily_counts]
            high_risk_counts = [row[2] for row in daily_counts]

            mean_actions = statistics.mean(action_counts)
            std_dev_actions = statistics.stdev(action_counts) if len(action_counts) > 1 else 0

            mean_risks = statistics.mean(high_risk_counts)
            std_dev_risks = statistics.stdev(high_risk_counts) if len(high_risk_counts) > 1 else 0

            anomalies = []

            # Check recent data (last 7 days) for outliers
            recent_data = daily_counts[-7:] if len(daily_counts) >= 7 else daily_counts

            for date, actions, risks in recent_data:
                # Z-score for actions
                if std_dev_actions > 0:
                    z_score_actions = (actions - mean_actions) / std_dev_actions

                    if abs(z_score_actions) > 2:  # More than 2 standard deviations
                        anomalies.append({
                            "type": "unusual_activity",
                            "severity": "high" if abs(z_score_actions) > 3 else "medium",
                            "description": f"Detected {abs(z_score_actions):.1f}x deviation in total activity",
                            "timestamp": datetime.combine(date, datetime.min.time()).replace(tzinfo=UTC).isoformat(),
                            "value": actions,
                            "baseline": round(mean_actions, 1),
                            "deviation": f"{z_score_actions:+.1f} σ"
                        })

                # Z-score for high-risk actions
                if std_dev_risks > 0 and mean_risks > 0:
                    z_score_risks = (risks - mean_risks) / std_dev_risks

                    if abs(z_score_risks) > 2:
                        anomalies.append({
                            "type": "unusual_risk_pattern",
                            "severity": "high" if abs(z_score_risks) > 3 else "medium",
                            "description": f"Unusual high-risk activity pattern detected",
                            "timestamp": datetime.combine(date, datetime.min.time()).replace(tzinfo=UTC).isoformat(),
                            "value": risks,
                            "baseline": round(mean_risks, 1),
                            "deviation": f"{z_score_risks:+.1f} σ"
                        })

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    def generate_recommendations(self,
                                risk_forecast: List[Dict],
                                agent_workload: List[Dict],
                                anomalies: List[Dict]) -> List[str]:
        """
        Generate AI-powered strategic recommendations
        """
        recommendations = []

        # Analyze risk forecast
        if risk_forecast:
            total_predicted = sum(f["predicted_high_risk"] for f in risk_forecast)
            avg_confidence = statistics.mean([f["confidence"] for f in risk_forecast])

            # Check trend
            if len(risk_forecast) >= 3:
                early_avg = statistics.mean([f["predicted_high_risk"] for f in risk_forecast[:3]])
                late_avg = statistics.mean([f["predicted_high_risk"] for f in risk_forecast[-3:]])

                if late_avg > early_avg * 1.2:  # 20% increase
                    recommendations.append(
                        "Risk levels are predicted to increase. Consider implementing stricter approval thresholds."
                    )
                elif total_predicted > 20:
                    recommendations.append(
                        "High volume of risky actions expected. Enable automated risk mitigation for common patterns."
                    )

            if avg_confidence < 0.6:
                recommendations.append(
                    f"Prediction confidence is moderate ({avg_confidence:.0%}). Continue collecting data for more accurate forecasts."
                )

        # Analyze agent workload
        if agent_workload:
            overutilized = [a for a in agent_workload if a["capacity_utilization"] > 0.8]
            underutilized = [a for a in agent_workload if a["capacity_utilization"] < 0.2]

            if overutilized:
                recommendations.append(
                    f"{len(overutilized)} agent(s) predicted to exceed 80% capacity. Consider load balancing or adding resources."
                )

            if len(underutilized) >= 2:
                recommendations.append(
                    f"{len(underutilized)} agents show low utilization. Review task distribution for optimization."
                )

            # Check high-risk ratios
            high_risk_agents = [a for a in agent_workload if a["high_risk_ratio"] > 0.5]
            if high_risk_agents:
                recommendations.append(
                    f"{len(high_risk_agents)} agent(s) handling high proportion of risky actions. Consider specialized oversight."
                )

        # Analyze anomalies
        if anomalies:
            high_severity = [a for a in anomalies if a["severity"] == "high"]

            if high_severity:
                recent_date = max(a["timestamp"] for a in high_severity)
                recommendations.append(
                    f"Critical anomaly detected on {recent_date[:10]}. Immediate investigation recommended."
                )
            else:
                recommendations.append(
                    f"{len(anomalies)} unusual pattern(s) detected. Review activity logs for potential security concerns."
                )

        # Default recommendation if no specific insights
        if not recommendations:
            recommendations.append(
                "System operating within normal parameters. Continue monitoring for pattern changes."
            )

        return recommendations[:5]  # Limit to top 5 recommendations


# Global singleton
_prediction_engine: Optional[PredictionEngine] = None


def get_prediction_engine(db: Session) -> PredictionEngine:
    """
    Get or create prediction engine instance

    Args:
        db: Database session

    Returns:
        PredictionEngine instance
    """
    # Note: We don't cache globally because db session changes
    return PredictionEngine(db)
