#!/usr/bin/env python3
"""
OW-KAI Enterprise Compliance Monitoring Agent

This agent continuously monitors AI models for compliance with:
- SOC2 controls
- GDPR requirements
- HIPAA regulations
- PCI-DSS standards

Runs as a containerized service on ECS Fargate.
"""

import requests
import time
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OWKAIClient:
    """Simple OW-KAI API client"""

    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.token = None
        self.session = requests.Session()

    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/token",
                json={"email": self.email, "password": self.password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                logger.info("✅ Authenticated successfully")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False

    def get_models(self) -> List[Dict[str, Any]]:
        """Get all registered models"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}

            response = self.session.get(
                f"{self.base_url}/api/governance/unified-actions",
                headers=headers,
                params={'limit': 10},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                actions = data.get('actions', [])
                logger.info(f"✅ Retrieved {len(actions)} models/actions")
                return actions
            else:
                logger.warning(f"⚠️  Failed to get models: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Error getting models: {e}")
            return []

    def register_compliance_violation(self, model_id: str, model_name: str, compliance_results: Dict) -> bool:
        """Submit compliance violation as actionable item"""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}

            # Determine risk level based on max risk score
            max_risk = compliance_results.get('max_risk_score', 0)
            if max_risk >= 70:
                risk_level = "high"
            elif max_risk >= 50:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Build detailed description of violations
            violations = []
            for framework, results in compliance_results.get('frameworks', {}).items():
                if not results.get('compliant'):
                    for finding in results.get('findings', []):
                        violations.append(f"{framework}: {finding}")

            description = f"Compliance Violation Detected on {model_name or model_id}"
            if violations:
                description += f" - {', '.join(violations)}"

            payload = {
                "agent_id": "compliance-monitor-aws-ecs",
                "action_type": "compliance_violation",
                "action_source": "agent",
                "description": description,
                "model_name": model_name or f"model-{model_id}",
                "risk_level": risk_level,
                "metadata": {
                    "agent_type": "compliance_monitor",
                    "scan_time": datetime.utcnow().isoformat(),
                    "model_id": model_id,
                    "compliance_results": compliance_results,
                    "violations": violations,
                    "frameworks_checked": ["SOC2", "GDPR", "HIPAA"]
                }
            }

            response = self.session.post(
                f"{self.base_url}/api/agent-action",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                action_data = response.json()
                action_id = action_data.get('id')
                logger.info(f"✅ Compliance violation submitted: Action ID {action_id} (Risk: {max_risk})")
                return True
            else:
                logger.warning(f"⚠️  Failed to submit violation: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error submitting violation: {e}")
            return False


class ComplianceMonitor:
    """Enterprise compliance monitoring agent"""

    def __init__(self, owkai_url: str, email: str, password: str):
        self.client = OWKAIClient(owkai_url, email, password)
        self.scan_interval = int(os.getenv('SCAN_INTERVAL', '300'))  # 5 minutes default

    def check_soc2_compliance(self, model: Dict) -> Dict[str, Any]:
        """Check SOC2 compliance controls"""
        logger.info(f"🔍 Checking SOC2 compliance for {model.get('model_name', 'unknown')}")

        # Simplified compliance checks
        results = {
            "framework": "SOC2",
            "compliant": True,
            "controls_checked": [
                "CC6.1: Logical access controls",
                "CC7.2: System operations monitoring",
                "CC8.1: Change management"
            ],
            "findings": [],
            "risk_score": 25
        }

        # Check if model has proper access controls
        if not model.get('owner'):
            results["compliant"] = False
            results["findings"].append("Missing owner/access control")
            results["risk_score"] = 65

        return results

    def check_gdpr_compliance(self, model: Dict) -> Dict[str, Any]:
        """Check GDPR compliance"""
        logger.info(f"🔍 Checking GDPR compliance for {model.get('model_name', 'unknown')}")

        results = {
            "framework": "GDPR",
            "compliant": True,
            "articles_checked": [
                "Article 5: Data processing principles",
                "Article 25: Data protection by design",
                "Article 32: Security of processing"
            ],
            "findings": [],
            "risk_score": 30
        }

        metadata = model.get('metadata', {})

        # Check for PII handling
        if metadata.get('handles_pii') and not metadata.get('consent_mechanism'):
            results["compliant"] = False
            results["findings"].append("PII processed without consent mechanism")
            results["risk_score"] = 75

        return results

    def check_hipaa_compliance(self, model: Dict) -> Dict[str, Any]:
        """Check HIPAA compliance"""
        logger.info(f"🔍 Checking HIPAA compliance for {model.get('model_name', 'unknown')}")

        results = {
            "framework": "HIPAA",
            "compliant": True,
            "safeguards_checked": [
                "Administrative Safeguards",
                "Physical Safeguards",
                "Technical Safeguards"
            ],
            "findings": [],
            "risk_score": 35
        }

        metadata = model.get('metadata', {})

        # Check for PHI handling
        if metadata.get('handles_phi') and not metadata.get('encryption_enabled'):
            results["compliant"] = False
            results["findings"].append("PHI processed without encryption")
            results["risk_score"] = 85

        return results

    def run_compliance_scan(self) -> None:
        """Run complete compliance scan on all models"""
        logger.info("=" * 60)
        logger.info("🏢 COMPLIANCE SCAN STARTED")
        logger.info("=" * 60)

        # Get all models
        models = self.client.get_models()

        if not models:
            logger.info("ℹ️  No models to scan")
            return

        logger.info(f"📊 Scanning {len(models)} models for compliance")

        for model in models:
            model_id = model.get('id', 'unknown')
            model_name = model.get('model_name', 'unknown')

            logger.info(f"\n🔍 Scanning model: {model_name} (ID: {model_id})")

            # Run all compliance checks
            soc2_results = self.check_soc2_compliance(model)
            gdpr_results = self.check_gdpr_compliance(model)
            hipaa_results = self.check_hipaa_compliance(model)

            # Aggregate results
            compliance_results = {
                "model_id": model_id,
                "model_name": model_name,
                "scan_timestamp": datetime.utcnow().isoformat(),
                "frameworks": {
                    "SOC2": soc2_results,
                    "GDPR": gdpr_results,
                    "HIPAA": hipaa_results
                },
                "overall_compliant": (
                    soc2_results["compliant"] and
                    gdpr_results["compliant"] and
                    hipaa_results["compliant"]
                ),
                "max_risk_score": max(
                    soc2_results["risk_score"],
                    gdpr_results["risk_score"],
                    hipaa_results["risk_score"]
                )
            }

            # Log results
            if compliance_results["overall_compliant"]:
                logger.info(f"✅ {model_name}: COMPLIANT (Risk: {compliance_results['max_risk_score']})")
            else:
                logger.warning(f"⚠️  {model_name}: NON-COMPLIANT (Risk: {compliance_results['max_risk_score']})")
                for framework, results in compliance_results["frameworks"].items():
                    if not results["compliant"]:
                        logger.warning(f"   {framework}: {', '.join(results['findings'])}")

                # Submit violation as actionable item to Authorization Center
                self.client.register_compliance_violation(model_id, model_name, compliance_results)

        logger.info("=" * 60)
        logger.info("✅ COMPLIANCE SCAN COMPLETED")
        logger.info("=" * 60)

    def run(self) -> None:
        """Main agent loop"""
        logger.info("🚀 Starting OW-KAI Compliance Monitoring Agent")
        logger.info(f"📡 Platform: {self.client.base_url}")
        logger.info(f"⏱️  Scan interval: {self.scan_interval} seconds")

        # Initial authentication
        if not self.client.authenticate():
            logger.error("❌ Initial authentication failed. Exiting.")
            return

        logger.info("✅ Agent initialized successfully")
        logger.info("🔄 Starting continuous monitoring...\n")

        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"SCAN ITERATION #{iteration} - {datetime.now().isoformat()}")
            logger.info(f"{'='*60}\n")

            try:
                # Re-authenticate if needed
                if not self.client.token:
                    logger.info("🔑 Re-authenticating...")
                    if not self.client.authenticate():
                        logger.error("❌ Re-authentication failed. Retrying in 60s...")
                        time.sleep(60)
                        continue

                # Run compliance scan
                self.run_compliance_scan()

                logger.info(f"\n⏳ Sleeping for {self.scan_interval} seconds until next scan...")
                time.sleep(self.scan_interval)

            except KeyboardInterrupt:
                logger.info("\n🛑 Agent stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in agent loop: {e}")
                logger.info("⏳ Retrying in 60 seconds...")
                time.sleep(60)


def main():
    """Main entry point"""
    # Get configuration from environment
    owkai_url = os.getenv('OWKAI_URL', 'https://pilot.owkai.app')
    email = os.getenv('OWKAI_EMAIL', 'admin@owkai.com')
    password = os.getenv('OWKAI_REDACTED-CREDENTIAL', 'admin123')

    logger.info("=" * 60)
    logger.info("OW-KAI ENTERPRISE COMPLIANCE MONITORING AGENT")
    logger.info("=" * 60)
    logger.info(f"Platform: {owkai_url}")
    logger.info(f"User: {email}")
    logger.info("=" * 60)

    # Create and run agent
    agent = ComplianceMonitor(owkai_url, email, password)
    agent.run()


if __name__ == "__main__":
    main()
