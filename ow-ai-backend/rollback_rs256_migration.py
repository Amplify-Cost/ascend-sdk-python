#!/usr/bin/env python3
"""
Rollback script for RS256 migration
Restores original HS256 implementation
"""

import shutil
import os
from pathlib import Path

def rollback_migration():
    """Rollback the RS256 migration"""
    project_root = Path("/Users/mac_001/OW_AI_Project")
    backup_dir = Path("/Users/mac_001/OW_AI_Project/backup_hs256_to_rs256_20250816_234920")
    
    print("🔄 Rolling back RS256 migration...")
    
    # Restore backed up files
    if backup_dir.exists():
        manifest_path = backup_dir / "backup_manifest.json"
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
        "jwt_manager.py",
        "jwks_routes.py", 
        "auth_dependencies.py",
        "test_rs256_migration.py"
    ]
    
    for file_name in created_files:
        file_path = project_root / file_name
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️  Removed: {file_name}")
    
    print("✅ Rollback completed")
    print(f"📁 Backup files preserved in: {backup_dir}")

if __name__ == "__main__":
    rollback_migration()
