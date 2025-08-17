#!/usr/bin/env python3
"""
Step 2 Rollback Script - Cookie Authentication
Restores Bearer token authentication
"""

import shutil
import os
from pathlib import Path

def rollback_step2():
    """Rollback Step 2 cookie authentication changes"""
    project_root = Path("/Users/mac_001/OW_AI_Project")
    backup_dir = Path("/Users/mac_001/OW_AI_Project/backup_step2_cookie_auth_20250817_005533")
    
    print("🔄 Rolling back Step 2 cookie authentication...")
    
    # Restore backed up files
    if backup_dir.exists():
        manifest_path = backup_dir / "step2_backup_manifest.json"
        if manifest_path.exists():
            import json
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            for file_path in manifest["backed_up_files"]:
                source = backup_dir / file_path
                target = project_root / file_path
                if source.exists():
                    shutil.copy2(source, target)
                    print(f"✅ Restored: {file_path}")
    
    # Remove created files
    created_files = [
        "ow-ai-backend/csrf_manager.py",
        "ow-ai-backend/cookie_auth.py"
    ]
    
    for file_name in created_files:
        file_path = project_root / file_name
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️  Removed: {file_name}")
    
    print("✅ Step 2 rollback completed")
    print("⚠️  You may need to restart your backend after rollback")

if __name__ == "__main__":
    rollback_step2()
