# Enterprise Codebase Organization Plan

## Current State Analysis
- **Total Files**: 308 items in root directory
- **Scripts**: 142 (46.1%) - TOO MANY IN ROOT
- **Temp Files**: 54 (17.5%) - SHOULD BE ARCHIVED
- **Backups**: 14 (4.5%) - SHOULD BE ARCHIVED
- **Docs**: 36 (11.7%) - SHOULD BE ORGANIZED

## Target Enterprise Structure
```
ow-ai-backend/
├── main.py                    # ✅ Main application entry
├── requirements.txt           # ✅ Dependencies
├── README.md                  # ✅ Project documentation
├── .env                       # ✅ Configuration
├── .gitignore                 # ✅ Git configuration
│
├── core/                      # ✅ KEEP - Infrastructure
├── models/                    # ✅ KEEP - Data models
├── routes/                    # ✅ KEEP - API routes
├── services/                  # ✅ KEEP - Business logic
├── schemas/                   # ✅ KEEP - Validation
├── middleware/                # ✅ KEEP - HTTP middleware
│
├── config/                    # 📁 CREATE - All config files
│   ├── config.py
│   ├── enterprise_config.py
│   └── aws_enterprise_config.py
│
├── scripts/                   # 📁 ORGANIZE - Utility scripts
│   ├── database/              # Database scripts
│   ├── deployment/            # Deployment scripts
│   ├── maintenance/           # Maintenance scripts
│   └── development/           # Development helpers
│
├── docs/                      # 📁 ORGANIZE - Documentation
│   ├── api/                   # API documentation
│   ├── architecture/          # Architecture docs
│   └── deployment/            # Deployment guides
│
├── tests/                     # ✅ KEEP - Test suite
├── migrations/                # ✅ KEEP - Database migrations
├── alembic/                   # ✅ KEEP - Alembic config
│
├── archive/                   # 📁 CREATE - Old/backup files
│   ├── backups/               # Backup files
│   ├── old-scripts/           # Old utility scripts
│   └── temp-files/            # Temporary development files
│
└── deployment/                # 📁 CREATE - Deployment configs
    ├── docker/                # Docker files
    ├── aws/                   # AWS configs
    └── kubernetes/            # K8s configs (future)
```

## Cleanup Actions

### Phase 1: Create New Structure (SAFE - No deletions)
```bash
mkdir -p config
mkdir -p scripts/{database,deployment,maintenance,development}
mkdir -p docs/{api,architecture,deployment}
mkdir -p archive/{backups,old-scripts,temp-files}
mkdir -p deployment/{docker,aws}
```

### Phase 2: Move Configuration Files
```bash
# Move config files
mv config.py config/ 2>/dev/null || true
mv enterprise_config.py config/ 2>/dev/null || true
mv aws_enterprise_config.py config/ 2>/dev/null || true
mv *.ini config/ 2>/dev/null || true
```

### Phase 3: Archive Backups (142 files → archive/)
```bash
# Move all .backup, .bak, .old files
find . -maxdepth 1 -name "*.backup*" -exec mv {} archive/backups/ \;
find . -maxdepth 1 -name "*.bak" -exec mv {} archive/backups/ \;
find . -maxdepth 1 -name "*.old*" -exec mv {} archive/backups/ \;
```

### Phase 4: Archive Temporary Files (54 files → archive/)
```bash
# Move temp/test/debug files
find . -maxdepth 1 -name "test_*.py" -exec mv {} archive/temp-files/ \;
find . -maxdepth 1 -name "temp_*.py" -exec mv {} archive/temp-files/ \;
find . -maxdepth 1 -name "debug_*.py" -exec mv {} archive/temp-files/ \;
find . -maxdepth 1 -name "fix_*.py" -exec mv {} archive/temp-files/ \;
find . -maxdepth 1 -name "add_*.py" -exec mv {} archive/temp-files/ \;
find . -maxdepth 1 -name "check_*.py" -exec mv {} archive/temp-files/ \;
```

### Phase 5: Organize Scripts (by purpose)
```bash
# Database scripts
mv *_db*.py scripts/database/ 2>/dev/null || true
mv *database*.py scripts/database/ 2>/dev/null || true
mv create_*.py scripts/database/ 2>/dev/null || true
mv migrate_*.py scripts/database/ 2>/dev/null || true
mv seed_*.py scripts/database/ 2>/dev/null || true
mv populate_*.py scripts/database/ 2>/dev/null || true

# Deployment scripts
mv deploy_*.py scripts/deployment/ 2>/dev/null || true
mv *deployment*.py scripts/deployment/ 2>/dev/null || true
mv *.sh scripts/deployment/ 2>/dev/null || true

# Development tools
mv analyze*.py scripts/development/ 2>/dev/null || true
mv audit*.py scripts/development/ 2>/dev/null || true
mv diagnose*.py scripts/development/ 2>/dev/null || true
mv validate*.py scripts/development/ 2>/dev/null || true
```

### Phase 6: Organize Documentation
```bash
# Move markdown docs
mv *.md docs/architecture/ 2>/dev/null || true
mv *.html docs/api/ 2>/dev/null || true
mv *.txt docs/ 2>/dev/null || true

# Move JSON reports
mv *_REPORT*.json docs/ 2>/dev/null || true
mv AUDIT*.json docs/ 2>/dev/null || true
```

### Phase 7: Organize Deployment Files
```bash
# Docker files
mv Dockerfile* deployment/docker/ 2>/dev/null || true

# AWS configs
mv aws*.* deployment/aws/ 2>/dev/null || true
mv *task*.json deployment/aws/ 2>/dev/null || true

# SQL schemas
mv *.sql scripts/database/ 2>/dev/null || true
```

## Files to Keep in Root (Production Essentials)
- main.py
- requirements.txt
- README.md
- .env (if exists)
- .gitignore
- pytest.ini
- core/, models/, routes/, services/, schemas/, middleware/
- tests/, migrations/, alembic/

## Safety Checks Before Execution
1. ✅ Commit current work to git
2. ✅ Create backup branch
3. ✅ Test imports after moves
4. ✅ Verify server still starts
5. ✅ Can rollback if needed

## Expected Results
- Root directory: ~20 essential files (from 308!)
- Clean, professional structure
- Easy to navigate
- Clear separation of concerns
- Production-ready organization
