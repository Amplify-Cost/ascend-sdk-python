# Complete Restore Procedures

## Quick Restore Commands

### Restore to Current Working State (V4 - Cookie Auth)
```bash
# Full restore of current working state
cp -r COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/current_working/* /path/to/project/
```

### Restore to Last Git Commit (V3 - Stable)  
```bash
# Restore to last committed state
git checkout d737e35
# OR restore from backup
cp -r COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/git_versions/SmartRule_Database_Alignment_d737e35/* /path/to/project/
```

### Restore to Original Enterprise Implementation (V1)
```bash
# Restore to original enterprise state
git checkout 894b585  
# OR restore from backup
cp -r COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/git_versions/Initial_Enterprise_JWT_Implementation_894b585/* /path/to/project/
```

## Detailed Restore Procedures

### 1. Emergency Production Rollback
If production deployment fails:

```bash
# 1. Stop services
railway down  # or your deployment command

# 2. Restore to last known working version
git checkout d737e35
railway up

# 3. If that fails, restore to original enterprise
git checkout 894b585
railway up
```

### 2. Development Environment Restore
If development environment breaks:

```bash
# 1. Backup current broken state
cp -r /current/project /broken/backup/$(date +%Y%m%d_%H%M%S)

# 2. Restore working cookie auth version
cp -r COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/current_working/* /current/project/

# 3. Restore configuration
cp COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/current_working/.env /current/project/
cp COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/current_working/ow-ai-dashboard/.env.local /current/project/ow-ai-dashboard/

# 4. Restart services
cd /current/project/ow-ai-backend && python3 main.py &
cd /current/project/ow-ai-dashboard && npm run dev &
```

### 3. Selective File Restore
Restore specific files from any version:

```bash
# Example: Restore original main.py from V1
cp COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/git_versions/Initial_Enterprise_JWT_Implementation_894b585/main.py /current/project/

# Example: Restore cookie auth fetchWithAuth.js from V4
cp COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/current_working/ow-ai-dashboard/src/utils/fetchWithAuth.js /current/project/ow-ai-dashboard/src/utils/
```

### 4. Configuration Restore
Restore specific configurations:

```bash
# Restore original enterprise config
cp COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/git_versions/Initial_Enterprise_JWT_Implementation_894b585/.env /current/project/

# Restore cookie auth config  
cp COMPLETE_VERSION_BACKUPS/ALL_VERSIONS_*/current_working/.env /current/project/
```

## Validation After Restore

### Check Git Status
```bash
git status
git log --oneline -5
```

### Test Backend
```bash
cd ow-ai-backend
python3 main.py
curl http://localhost:8000/health
```

### Test Frontend
```bash
cd ow-ai-dashboard  
npm run dev
# Test login at http://localhost:5174
```

### Verify Authentication
- [ ] Login works
- [ ] Dashboard loads
- [ ] API calls succeed
- [ ] Expected auth method (JWT vs Cookie)

## Recovery Verification Checklist

### After V1 Restore (Original Enterprise)
- [ ] RS256 JWT working
- [ ] AWS Secrets Manager connected  
- [ ] JWKS endpoint accessible
- [ ] Basic authentication functional

### After V3 Restore (Last Commit)
- [ ] All V1 features working
- [ ] Database schema updates applied
- [ ] SmartRule model aligned
- [ ] No breaking changes

### After V4 Restore (Cookie Auth)
- [ ] All previous features working
- [ ] Cookie authentication functional
- [ ] CSRF protection active
- [ ] No localStorage token storage
- [ ] Enterprise security standards met

## Emergency Contacts

- **Technical Issues:** engineering@ow-ai.com
- **Security Concerns:** security@ow-ai.com  
- **Infrastructure:** devops@ow-ai.com
- **Emergency Hotline:** +1-XXX-XXX-XXXX
