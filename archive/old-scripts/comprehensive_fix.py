with open('routes/unified_governance_routes.py', 'r') as f:
    content = f.read()

# Fix 1: Ensure CVSS calculation is properly wrapped in try-except
import re

# Find the CVSS calculation section and ensure it's properly structured
cvss_pattern = r'(cvss_result = cvss_mapper\.auto_assess_action\([^)]+\))'
cvss_replacement = r'''try:
                    \1
                    if cvss_result and 'risk_score' in cvss_result:
                        action.risk_score = cvss_result['risk_score']
                    else:
                        risk_scores = {"low": 30, "medium": 50, "high": 70, "critical": 90}
                        action.risk_score = risk_scores.get(action.risk_level, 50)
                    db.commit()
                except Exception as e:
                    logger.warning(f"CVSS calculation failed for action {action.id}: {e}")
                    action.risk_score = 50'''

content = re.sub(cvss_pattern, cvss_replacement, content)

with open('routes/unified_governance_routes.py', 'w') as f:
    f.write(content)

print("✅ Applied comprehensive fixes to unified_governance_routes.py")
