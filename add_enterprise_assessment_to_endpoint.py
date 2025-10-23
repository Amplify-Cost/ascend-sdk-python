#!/usr/bin/env python3
"""
Add enterprise assessment calls to /agent-action endpoint
"""

with open('main.py', 'r') as f:
    content = f.read()

# Find the endpoint and add assessment calls after action_id is created
old_code = '''            # Get the inserted action ID
            action_id = result.fetchone()[0]
            
            db.commit()
            
            # Enterprise audit logging
            logger.info(f"✅ Enterprise action submitted: ID={action_id}, Agent={data['agent_id']}, User={current_user.get('email', 'unknown')}")'''

new_code = '''            # Get the inserted action ID
            action_id = result.fetchone()[0]
            
            db.commit()
            
            # === ENTERPRISE RISK ASSESSMENT ===
            try:
                from services.cvss_auto_mapper import cvss_auto_mapper
                from services.mitre_mapper import mitre_mapper
                from services.nist_mapper import nist_mapper
                
                # 1. CVSS Assessment
                cvss_result = cvss_auto_mapper.auto_assess_action(
                    db=db,
                    action_id=action_id,
                    action_type=data["action_type"],
                    context=data.get("context", {})
                )
                
                # 2. MITRE Mapping
                mitre_result = mitre_mapper.map_action_to_techniques(
                    db=db,
                    action_id=action_id,
                    action_type=data["action_type"]
                )
                
                # 3. NIST Mapping
                nist_result = nist_mapper.map_action_to_controls(
                    db=db,
                    action_id=action_id,
                    action_type=data["action_type"]
                )
                
                # 4. Update risk_score based on CVSS
                if cvss_result and 'base_score' in cvss_result:
                    risk_score = min(int(cvss_result['base_score'] * 10), 100)
                    db.execute(text("UPDATE agent_actions SET risk_score = :score WHERE id = :id"), 
                              {"score": risk_score, "id": action_id})
                    db.commit()
                
                logger.info(f"✅ Enterprise assessment complete: ID={action_id}, CVSS={cvss_result.get('base_score', 'N/A')}, MITRE={len(mitre_result.get('techniques', []))}, NIST={len(nist_result.get('controls', []))}")
                
            except Exception as assessment_error:
                logger.warning(f"⚠️ Enterprise assessment failed for action {action_id}: {str(assessment_error)}")
                # Don't fail the submission if assessment fails
            
            # Enterprise audit logging
            logger.info(f"✅ Enterprise action submitted: ID={action_id}, Agent={data['agent_id']}, User={current_user.get('email', 'unknown')}")'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('main.py', 'w') as f:
        f.write(content)
    print("✅ Added enterprise assessment to /agent-action endpoint")
    print("✅ Backup created: main.py.backup_*")
    print("\n🔄 IMPORTANT: Restart your backend server for changes to take effect!")
else:
    print("❌ Could not find the target code section")
    print("The endpoint may have changed. Manual update needed.")
