"""
Enterprise Risk Scoring Configuration Loader
Loads active configuration from database with caching

Engineer: Donald King (OW-kai Enterprise)
Created: 2025-11-14
"""
from sqlalchemy.orm import Session
from models import RiskScoringConfig
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# In-memory cache (refreshed every 60 seconds)
_config_cache: Optional[Dict] = None
_cache_timestamp: Optional[float] = None
CACHE_TTL_SECONDS = 60

def get_active_risk_config(db: Session) -> Optional[Dict]:
    """
    Get active risk scoring configuration from database

    Args:
        db: SQLAlchemy database session

    Returns:
        Dict with all weight configurations
        None if no active config found (caller should use hardcoded defaults)
    """
    import time

    global _config_cache, _cache_timestamp

    # Check cache first (performance optimization)
    current_time = time.time()
    if _config_cache and _cache_timestamp:
        if (current_time - _cache_timestamp) < CACHE_TTL_SECONDS:
            logger.debug("Using cached risk config (cache hit)")
            return _config_cache

    # Query database for active config
    try:
        active_config = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_active == True
        ).first()

        if active_config:
            logger.info(f"Loaded risk config v{active_config.config_version} from database")

            config_dict = {
                "config_version": active_config.config_version,
                "algorithm_version": active_config.algorithm_version,
                "environment_weights": active_config.environment_weights,
                "action_weights": active_config.action_weights,
                "resource_multipliers": active_config.resource_multipliers,
                "pii_weights": active_config.pii_weights,
                "component_percentages": active_config.component_percentages,
                "description": active_config.description
            }

            # Update cache
            _config_cache = config_dict
            _cache_timestamp = current_time

            return config_dict

        else:
            logger.warning("No active risk config found in database, using hardcoded defaults")
            return None

    except Exception as e:
        logger.error(f"Error loading risk config from database: {e}")
        return None

def clear_config_cache():
    """Clear the configuration cache (called after config updates)"""
    global _config_cache, _cache_timestamp
    _config_cache = None
    _cache_timestamp = None
    logger.info("Risk config cache cleared")
