#!/bin/bash

################################################################################
# OW AI - Master Remediation Script
#
# This script orchestrates all fixes from the code review remediation plan.
#
# SAFETY FEATURES:
# - Runs locally only (no production deployment)
# - Creates backups before each phase
# - Tests after each change
# - Automatic rollback on failure
# - Git commits (no push)
#
# Usage:
#   ./master-fix-script.sh --dry-run    # Show what will be done
#   ./master-fix-script.sh --execute    # Run all fixes
#   ./master-fix-script.sh --phase 1    # Run specific phase only
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/mac_001/OW_AI_Project"
SCRIPT_DIR="$PROJECT_ROOT/scripts/automated-fixes"
BACKUP_DIR="$PROJECT_ROOT/backups"
REPORTS_DIR="$PROJECT_ROOT/scripts/automated-fixes/reports"
LOGS_DIR="$PROJECT_ROOT/scripts/automated-fixes/logs"

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="$BACKUP_DIR/${TIMESTAMP}_automated_fixes"

# Flags
DRY_RUN=false
EXECUTE=false
SPECIFIC_PHASE=""
SKIP_TESTS=false

################################################################################
# Utility Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGS_DIR/master-${TIMESTAMP}.log"
}

################################################################################
# Pre-flight Checks
################################################################################

check_prerequisites() {
    print_header "Pre-flight Checks"

    log "Checking prerequisites..."

    # Check if in correct directory
    if [ ! -d "$PROJECT_ROOT" ]; then
        print_error "Project directory not found: $PROJECT_ROOT"
        exit 1
    fi
    print_success "Project directory found"

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found. Please install Node.js 18+"
        exit 1
    fi
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm not found"
        exit 1
    fi
    print_success "npm found: $(npm --version)"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"

    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git not found"
        exit 1
    fi
    print_success "Git found: $(git --version)"

    # Check if in git repo
    cd "$PROJECT_ROOT"
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi
    print_success "Git repository detected"

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_warning "Uncommitted changes detected"
        if [ "$DRY_RUN" = false ] && [ "$EXECUTE" = true ]; then
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Aborted by user"
                exit 1
            fi
        fi
    else
        print_success "Working directory clean"
    fi

    # Create necessary directories
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$LOGS_DIR"
    print_success "Directories created"

    log "All prerequisites met"
}

################################################################################
# Backup Functions
################################################################################

create_backup() {
    print_header "Creating Backup"

    log "Creating backup at: $BACKUP_PATH"

    mkdir -p "$BACKUP_PATH"

    # Backup source code
    log "Backing up frontend..."
    rsync -a --exclude=node_modules --exclude=dist --exclude=.vite \
        "$PROJECT_ROOT/owkai-pilot-frontend/" \
        "$BACKUP_PATH/owkai-pilot-frontend/"

    rsync -a --exclude=node_modules --exclude=dist --exclude=.vite \
        "$PROJECT_ROOT/src/" \
        "$BACKUP_PATH/src/" 2>/dev/null || true

    log "Backing up backend..."
    rsync -a --exclude=__pycache__ --exclude=*.pyc --exclude=venv \
        "$PROJECT_ROOT/ow-ai-backend/" \
        "$BACKUP_PATH/ow-ai-backend/"

    # Create backup manifest
    cat > "$BACKUP_PATH/MANIFEST.txt" <<EOF
Backup created: $(date)
Git commit: $(git rev-parse HEAD)
Git branch: $(git rev-parse --abbrev-ref HEAD)

Frontend files: $(find "$BACKUP_PATH/owkai-pilot-frontend" -type f | wc -l)
Backend files: $(find "$BACKUP_PATH/ow-ai-backend" -type f | wc -l)

Restore with: ./utils/rollback.sh $TIMESTAMP
EOF

    print_success "Backup created: $BACKUP_PATH"
    log "Backup manifest created"
}

################################################################################
# Phase Execution
################################################################################

run_phase_1() {
    print_header "Phase 1: Security & Cleanup"

    log "Starting Phase 1..."

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: Would execute phase1-security-cleanup.sh"
        return 0
    fi

    # Create phase backup
    PHASE_BACKUP="${BACKUP_PATH}_phase1"
    create_backup

    # Execute phase 1 script
    log "Executing phase 1 script..."
    if bash "$SCRIPT_DIR/phase1-security-cleanup.sh"; then
        print_success "Phase 1 completed successfully"

        # Run tests
        if [ "$SKIP_TESTS" = false ]; then
            log "Running Phase 1 tests..."
            if bash "$SCRIPT_DIR/utils/test-runner.sh" --phase 1; then
                print_success "Phase 1 tests passed"
            else
                print_error "Phase 1 tests failed - Rolling back"
                bash "$SCRIPT_DIR/utils/rollback.sh" "$TIMESTAMP"
                exit 1
            fi
        fi

        # Git commit
        git add .
        git commit -m "Phase 1: Security & Cleanup - Automated fixes" || true
        print_success "Phase 1 committed to git"

    else
        print_error "Phase 1 failed - Rolling back"
        bash "$SCRIPT_DIR/utils/rollback.sh" "$TIMESTAMP"
        exit 1
    fi
}

run_phase_2() {
    print_header "Phase 2: Performance Optimization"

    log "Starting Phase 2..."

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: Would execute phase2-performance.sh"
        return 0
    fi

    # Create phase backup
    PHASE_BACKUP="${BACKUP_PATH}_phase2"
    create_backup

    # Execute phase 2 script
    log "Executing phase 2 script..."
    if bash "$SCRIPT_DIR/phase2-performance.sh"; then
        print_success "Phase 2 completed successfully"

        # Run tests
        if [ "$SKIP_TESTS" = false ]; then
            log "Running Phase 2 tests..."
            if bash "$SCRIPT_DIR/utils/test-runner.sh" --phase 2; then
                print_success "Phase 2 tests passed"
            else
                print_error "Phase 2 tests failed - Rolling back"
                bash "$SCRIPT_DIR/utils/rollback.sh" "${TIMESTAMP}_phase2"
                exit 1
            fi
        fi

        # Git commit
        git add .
        git commit -m "Phase 2: Performance Optimization - Automated fixes" || true
        print_success "Phase 2 committed to git"

    else
        print_error "Phase 2 failed - Rolling back"
        bash "$SCRIPT_DIR/utils/rollback.sh" "${TIMESTAMP}_phase2"
        exit 1
    fi
}

run_phase_3() {
    print_header "Phase 3: Architecture Improvements"

    log "Starting Phase 3..."

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: Would execute phase3-architecture.sh"
        return 0
    fi

    # Create phase backup
    PHASE_BACKUP="${BACKUP_PATH}_phase3"
    create_backup

    # Execute phase 3 script
    log "Executing phase 3 script..."
    if bash "$SCRIPT_DIR/phase3-architecture.sh"; then
        print_success "Phase 3 completed successfully"

        # Run tests
        if [ "$SKIP_TESTS" = false ]; then
            log "Running Phase 3 tests..."
            if bash "$SCRIPT_DIR/utils/test-runner.sh" --phase 3; then
                print_success "Phase 3 tests passed"
            else
                print_error "Phase 3 tests failed - Rolling back"
                bash "$SCRIPT_DIR/utils/rollback.sh" "${TIMESTAMP}_phase3"
                exit 1
            fi
        fi

        # Git commit
        git add .
        git commit -m "Phase 3: Architecture Improvements - Automated fixes" || true
        print_success "Phase 3 committed to git"

    else
        print_error "Phase 3 failed - Rolling back"
        bash "$SCRIPT_DIR/utils/rollback.sh" "${TIMESTAMP}_phase3"
        exit 1
    fi
}

run_phase_4() {
    print_header "Phase 4: Testing & Validation"

    log "Starting Phase 4..."

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: Would execute phase4-testing.sh"
        return 0
    fi

    # Execute phase 4 script (testing only, no changes)
    log "Executing phase 4 script..."
    if bash "$SCRIPT_DIR/phase4-testing.sh"; then
        print_success "Phase 4 completed successfully"
    else
        print_error "Phase 4 failed - Some tests did not pass"
        exit 1
    fi
}

################################################################################
# Main Execution
################################################################################

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --execute)
                EXECUTE=true
                shift
                ;;
            --phase)
                SPECIFIC_PHASE="$2"
                EXECUTE=true
                shift 2
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --help)
                cat <<EOF
OW AI Master Remediation Script

Usage:
  $0 --dry-run              Show what will be done (no changes)
  $0 --execute              Run all phases with testing
  $0 --phase N              Run specific phase only (1-4)
  $0 --skip-tests           Skip automated tests (faster but risky)
  $0 --help                 Show this help

Phases:
  1 - Security & Cleanup (2-3 hours)
  2 - Performance Optimization (3-4 hours)
  3 - Architecture Improvements (2-3 hours)
  4 - Testing & Validation (1-2 hours)

Examples:
  $0 --dry-run                    # Preview all changes
  $0 --execute                    # Run everything
  $0 --phase 1                    # Run only phase 1
  $0 --phase 2 --skip-tests       # Run phase 2, skip tests
EOF
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Validate flags
    if [ "$DRY_RUN" = false ] && [ "$EXECUTE" = false ]; then
        print_error "Must specify --dry-run or --execute"
        echo "Use --help for usage information"
        exit 1
    fi
}

main() {
    print_header "OW AI - Automated Remediation Script"

    echo "Project: OW AI Enterprise Authorization Center"
    echo "Timestamp: $TIMESTAMP"
    echo "Mode: $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "EXECUTE")"
    echo ""

    # Parse command line arguments
    parse_arguments "$@"

    # Run pre-flight checks
    check_prerequisites

    # Create initial backup (only if executing)
    if [ "$EXECUTE" = true ] && [ "$DRY_RUN" = false ]; then
        create_backup
    fi

    # Run phases
    if [ -n "$SPECIFIC_PHASE" ]; then
        case $SPECIFIC_PHASE in
            1)
                run_phase_1
                ;;
            2)
                run_phase_2
                ;;
            3)
                run_phase_3
                ;;
            4)
                run_phase_4
                ;;
            *)
                print_error "Invalid phase: $SPECIFIC_PHASE (must be 1-4)"
                exit 1
                ;;
        esac
    else
        # Run all phases
        run_phase_1
        run_phase_2
        run_phase_3
        run_phase_4
    fi

    # Final summary
    print_header "Execution Complete"

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN completed - no changes made"
        print_info "Run with --execute to apply changes"
    else
        print_success "All phases completed successfully!"
        print_success "Backup location: $BACKUP_PATH"
        print_info "Review reports in: $REPORTS_DIR"
        print_info "Review logs in: $LOGS_DIR"

        echo ""
        echo "Next Steps:"
        echo "  1. Review reports in $REPORTS_DIR"
        echo "  2. Test application manually"
        echo "  3. Run: npm start (frontend) and python main.py (backend)"
        echo "  4. If issues found: ./utils/rollback.sh $TIMESTAMP"
    fi

    log "Script execution completed"
}

# Run main function with all arguments
main "$@"
