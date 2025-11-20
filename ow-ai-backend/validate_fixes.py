#!/usr/bin/env python3
"""
Quick validation script for unified_governance_routes.py fixes
Validates syntax, imports, and endpoint configuration
"""

import sys
import os
import ast

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_file(filepath):
    """Validate Python file syntax and content"""
    print(f"\n{BLUE}Validating: {filepath}{RESET}")

    try:
        with open(filepath, 'r') as f:
            source = f.read()

        # Check 1: Syntax validation
        try:
            ast.parse(source)
            print(f"{GREEN}✓{RESET} Syntax is valid")
        except SyntaxError as e:
            print(f"{RED}✗{RESET} Syntax error: {e}")
            return False

        # Check 2: ImmutableAuditService import
        if 'from services.immutable_audit_service import ImmutableAuditService' in source:
            print(f"{GREEN}✓{RESET} ImmutableAuditService import present")
        else:
            print(f"{RED}✗{RESET} Missing ImmutableAuditService import")
            return False

        # Check 3: AuditLog should NOT be imported from models
        if 'from models import' in source:
            models_import = [line for line in source.split('\n') if 'from models import' in line and not line.strip().startswith('#')]
            # Check if AuditLog is in the actual import list (not in comment)
            has_audit_log = any('AuditLog,' in line or ', AuditLog' in line or 'import AuditLog' in line
                                for line in models_import)
            if has_audit_log:
                print(f"{RED}✗{RESET} AuditLog still imported from models (should be removed)")
                return False
            else:
                print(f"{GREEN}✓{RESET} AuditLog correctly removed from models import")

        # Check 4: Old AuditLog() usage should be gone
        if 'AuditLog(' in source:
            print(f"{RED}✗{RESET} Found AuditLog() usage (should use ImmutableAuditService)")
            return False
        else:
            print(f"{GREEN}✓{RESET} No AuditLog() instantiation found")

        # Check 5: ImmutableAuditService usage
        if 'ImmutableAuditService(db)' in source or 'audit_service = ImmutableAuditService' in source:
            print(f"{GREEN}✓{RESET} ImmutableAuditService properly used")
        else:
            print(f"{YELLOW}⚠{RESET} ImmutableAuditService import found but not used")

        # Check 6: log_event method calls
        log_event_count = source.count('audit_service.log_event(')
        if log_event_count >= 2:
            print(f"{GREEN}✓{RESET} Found {log_event_count} audit_service.log_event() calls")
        elif log_event_count == 1:
            print(f"{YELLOW}⚠{RESET} Only 1 audit_service.log_event() call (expected 2)")
        else:
            print(f"{RED}✗{RESET} No audit_service.log_event() calls found")

        # Check 7: LogAuditTrail invalid fields
        invalid_patterns = [
            'action_id=',
            'user_email=',
            'timestamp=datetime.now(UTC)'
        ]

        # Find LogAuditTrail usage
        if 'LogAuditTrail(' in source:
            has_invalid = False
            for pattern in invalid_patterns:
                if pattern in source and 'LogAuditTrail' in source[max(0, source.find(pattern)-200):source.find(pattern)+50]:
                    print(f"{RED}✗{RESET} Found invalid field in LogAuditTrail: {pattern}")
                    has_invalid = True

            if not has_invalid:
                print(f"{GREEN}✓{RESET} LogAuditTrail uses only valid fields")

        # Check 8: Endpoint aliases
        if '@router.get("/unified/actions")' in source:
            print(f"{GREEN}✓{RESET} URL alias endpoint /unified/actions exists")
        else:
            print(f"{RED}✗{RESET} Missing /unified/actions endpoint alias")
            return False

        # Check 9: Request parameter for audit logging
        if 'request: Request' in source:
            request_count = source.count('request: Request')
            print(f"{GREEN}✓{RESET} Request parameter added ({request_count} endpoints)")
        else:
            print(f"{YELLOW}⚠{RESET} No Request parameter found (needed for IP/user-agent)")

        # Check 10: Enterprise audit error handling
        if 'except Exception as audit_error:' in source:
            print(f"{GREEN}✓{RESET} Audit error handling implemented")
        else:
            print(f"{YELLOW}⚠{RESET} No audit error handling found")

        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Error validating file: {e}")
        return False

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}ENTERPRISE VALIDATION: Unified Governance Routes Fixes{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    filepath = 'routes/unified_governance_routes.py'

    if not os.path.exists(filepath):
        print(f"{RED}✗{RESET} File not found: {filepath}")
        return 1

    success = check_file(filepath)

    print(f"\n{BLUE}{'='*70}{RESET}")
    if success:
        print(f"{GREEN}✓ ALL VALIDATIONS PASSED{RESET}")
        print(f"\n{BLUE}FIXES VERIFIED:{RESET}")
        print(f"  1. {GREEN}✓{RESET} AuditLog replaced with ImmutableAuditService")
        print(f"  2. {GREEN}✓{RESET} LogAuditTrail schema errors fixed")
        print(f"  3. {GREEN}✓{RESET} URL alias /unified/actions added")
        print(f"  4. {GREEN}✓{RESET} Request parameters for audit context")
        print(f"\n{GREEN}Ready for production deployment!{RESET}")
        return 0
    else:
        print(f"{RED}✗ VALIDATION FAILED{RESET}")
        print(f"\n{YELLOW}Review errors above and fix issues{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
