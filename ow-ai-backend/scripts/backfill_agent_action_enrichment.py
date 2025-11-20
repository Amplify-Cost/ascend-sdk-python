"""
Backfill CVSS/MITRE/NIST enrichment for existing agent actions
Created: 2025-11-12
Purpose: Recalculate security enrichment for actions created before services existed
"""
import logging
import sys
import os
from datetime import datetime, UTC

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import AgentAction
from enrichment import evaluate_action_enrichment
from services.cvss_auto_mapper import cvss_auto_mapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_single_action(db, action):
    """Backfill enrichment for a single action"""
    try:
        logger.info(f"Processing action {action.id}: {action.agent_id} - {action.action_type}")

        # Recalculate enrichment
        enrichment = evaluate_action_enrichment(
            action_type=action.action_type,
            description=action.description or "",
            db=db,
            action_id=action.id,
            context={
                "tool_name": action.tool_name,
                "user_id": action.user_id
            }
        )

        # Update action with enrichment results
        action.risk_level = enrichment["risk_level"]
        action.mitre_tactic = enrichment["mitre_tactic"]
        action.mitre_technique = enrichment["mitre_technique"]
        action.nist_control = enrichment["nist_control"]
        action.nist_description = enrichment["nist_description"]
        action.recommendation = enrichment["recommendation"]
        action.cvss_score = enrichment.get("cvss_score")
        action.cvss_severity = enrichment.get("cvss_severity")
        action.cvss_vector = enrichment.get("cvss_vector")
        action.risk_score = (
            enrichment.get("cvss_score") * 10
            if enrichment.get("cvss_score")
            else None
        )
        action.updated_at = datetime.now(UTC)

        # Commit changes
        db.commit()
        db.refresh(action)

        logger.info(
            f"✅ Backfilled action {action.id}: "
            f"CVSS {action.cvss_score} ({action.cvss_severity}), "
            f"MITRE {action.mitre_tactic}, "
            f"NIST {action.nist_control}"
        )

        return True

    except Exception as e:
        logger.error(f"❌ Failed to backfill action {action.id}: {e}", exc_info=True)
        db.rollback()
        return False


def backfill_all_actions(dry_run=False, limit=None):
    """Backfill enrichment for all actions with NULL values"""
    db = SessionLocal()

    try:
        # Find actions needing backfill
        query = db.query(AgentAction).filter(
            (AgentAction.cvss_score == None) |
            (AgentAction.mitre_tactic == None) |
            (AgentAction.nist_control == None)
        ).order_by(AgentAction.id)

        if limit:
            query = query.limit(limit)

        actions_to_backfill = query.all()

        logger.info(f"Found {len(actions_to_backfill)} actions to backfill")

        if len(actions_to_backfill) == 0:
            logger.info("✅ No actions need backfilling - all up to date!")
            return

        if dry_run:
            logger.info("DRY RUN MODE - showing what would be backfilled:")
            for action in actions_to_backfill:
                logger.info(
                    f"  - Action {action.id}: {action.agent_id} - {action.action_type} "
                    f"(CVSS: {action.cvss_score}, MITRE: {action.mitre_tactic}, "
                    f"NIST: {action.nist_control})"
                )
            logger.info(f"\nRun without --dry-run to perform backfill")
            return

        # Backfill each action
        success_count = 0
        failure_count = 0

        for idx, action in enumerate(actions_to_backfill, 1):
            logger.info(f"\n[{idx}/{len(actions_to_backfill)}] Processing action {action.id}")

            if backfill_single_action(db, action):
                success_count += 1
            else:
                failure_count += 1

        # Summary
        logger.info("\n" + "="*80)
        logger.info("BACKFILL COMPLETE")
        logger.info("="*80)
        logger.info(f"Total actions processed: {len(actions_to_backfill)}")
        logger.info(f"✅ Successfully backfilled: {success_count}")
        logger.info(f"❌ Failed: {failure_count}")

        if failure_count > 0:
            logger.warning(f"\n⚠️  {failure_count} actions failed - check logs above for details")

    except Exception as e:
        logger.error(f"Critical error during backfill: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


def verify_backfill():
    """Verify backfill completed successfully"""
    db = SessionLocal()

    try:
        # Count actions with NULL values
        null_cvss = db.query(AgentAction).filter(AgentAction.cvss_score == None).count()
        null_mitre = db.query(AgentAction).filter(AgentAction.mitre_tactic == None).count()
        null_nist = db.query(AgentAction).filter(AgentAction.nist_control == None).count()

        total_actions = db.query(AgentAction).count()
        with_cvss = db.query(AgentAction).filter(AgentAction.cvss_score != None).count()
        with_mitre = db.query(AgentAction).filter(AgentAction.mitre_tactic != None).count()
        with_nist = db.query(AgentAction).filter(AgentAction.nist_control != None).count()

        logger.info("\n" + "="*80)
        logger.info("VERIFICATION RESULTS")
        logger.info("="*80)
        logger.info(f"Total actions: {total_actions}")
        logger.info(f"Actions with CVSS: {with_cvss} ({with_cvss/total_actions*100:.1f}%)")
        logger.info(f"Actions with MITRE: {with_mitre} ({with_mitre/total_actions*100:.1f}%)")
        logger.info(f"Actions with NIST: {with_nist} ({with_nist/total_actions*100:.1f}%)")
        logger.info(f"\nActions with NULL CVSS: {null_cvss}")
        logger.info(f"Actions with NULL MITRE: {null_mitre}")
        logger.info(f"Actions with NULL NIST: {null_nist}")

        if null_cvss == 0 and null_mitre == 0 and null_nist == 0:
            logger.info("\n✅ ALL ACTIONS HAVE COMPLETE ENRICHMENT DATA!")
        else:
            logger.warning(f"\n⚠️  {null_cvss + null_mitre + null_nist} NULL values remain")

        # Show sample enriched actions
        sample_actions = db.query(AgentAction).filter(
            AgentAction.cvss_score != None
        ).limit(5).all()

        if sample_actions:
            logger.info("\nSample enriched actions:")
            for action in sample_actions:
                logger.info(
                    f"  - Action {action.id}: CVSS {action.cvss_score} ({action.cvss_severity}), "
                    f"MITRE {action.mitre_tactic}, NIST {action.nist_control}"
                )

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Backfill agent action enrichment')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be backfilled without making changes')
    parser.add_argument('--verify', action='store_true', help='Verify backfill completed successfully')
    parser.add_argument('--limit', type=int, help='Limit number of actions to backfill (for testing)')

    args = parser.parse_args()

    if args.verify:
        verify_backfill()
    else:
        backfill_all_actions(dry_run=args.dry_run, limit=args.limit)
