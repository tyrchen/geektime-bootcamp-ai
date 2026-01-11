#!/bin/bash
#
# Codex Code Review Helper Script
#
# Usage:
#   ./review.sh [options]
#
# Options:
#   --staged          Review staged git changes (default)
#   --unstaged        Review all uncommitted changes
#   --branch <name>   Review changes compared to branch
#   --files <files>   Review specific files (comma-separated)
#   --dir <path>      Review entire directory
#   --pr <number>     Review GitHub PR (requires gh CLI)
#   --security        Focus on security audit
#   --performance     Focus on performance review
#   --output <file>   Save review to file
#   --model <model>   Use specific model (e.g., o3)
#   --help            Show this help message
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REVIEW_TYPE="staged"
OUTPUT_FILE=""
MODEL=""
BRANCH="main"
FILES=""
DIR=""
PR_NUMBER=""
FOCUS=""

print_help() {
    head -25 "$0" | tail -22 | sed 's/^# //' | sed 's/^#//'
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

check_codex() {
    if ! command -v codex &> /dev/null; then
        log_error "Codex CLI is not installed."
        echo "Install with: npm install -g @openai/codex"
        echo "Or: brew install --cask codex"
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --staged)
            REVIEW_TYPE="staged"
            shift
            ;;
        --unstaged)
            REVIEW_TYPE="unstaged"
            shift
            ;;
        --branch)
            REVIEW_TYPE="branch"
            BRANCH="$2"
            shift 2
            ;;
        --files)
            REVIEW_TYPE="files"
            FILES="$2"
            shift 2
            ;;
        --dir)
            REVIEW_TYPE="dir"
            DIR="$2"
            shift 2
            ;;
        --pr)
            REVIEW_TYPE="pr"
            PR_NUMBER="$2"
            shift 2
            ;;
        --security)
            FOCUS="security"
            shift
            ;;
        --performance)
            FOCUS="performance"
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --help|-h)
            print_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

check_codex

# Build the prompt based on review type and focus
build_prompt() {
    local base_prompt=""
    local focus_prompt=""

    # Focus-specific additions
    if [[ "$FOCUS" == "security" ]]; then
        focus_prompt="Focus primarily on security issues:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Command injection risks
- Authentication/authorization flaws
- Sensitive data exposure
- Input validation issues
- Hardcoded secrets/credentials

Rate severity: Critical / High / Medium / Low"
    elif [[ "$FOCUS" == "performance" ]]; then
        focus_prompt="Focus primarily on performance issues:
- Algorithm complexity (O(n^2) or worse)
- Memory leaks
- N+1 query patterns
- Unnecessary allocations
- Missing caching opportunities
- Blocking operations

Provide specific optimization suggestions."
    else
        focus_prompt="Provide a comprehensive review covering:
1. Code correctness and logic errors
2. Security vulnerabilities
3. Performance concerns
4. Code quality and maintainability
5. Error handling completeness

Rate each finding: Critical / High / Medium / Low
Provide specific file:line references and fix suggestions."
    fi

    case $REVIEW_TYPE in
        staged)
            base_prompt="Review all staged git changes (git diff --cached).

$focus_prompt"
            ;;
        unstaged)
            base_prompt="Review all uncommitted changes (git diff HEAD).

$focus_prompt"
            ;;
        branch)
            base_prompt="Review changes between $BRANCH and current branch (git diff $BRANCH...HEAD).

$focus_prompt"
            ;;
        files)
            base_prompt="Review these files: $FILES

$focus_prompt"
            ;;
        dir)
            base_prompt="Review all code in the $DIR directory.

$focus_prompt"
            ;;
        pr)
            base_prompt="Review the code changes in /tmp/pr_${PR_NUMBER}_diff.txt as a thorough PR reviewer.

## Summary
Brief description of what this PR accomplishes

## Code Review
For each file changed:
- Purpose of changes
- Potential issues (bugs, edge cases)
- Security considerations
- Performance implications

## Recommendations
- Required changes (blocking)
- Suggested improvements (non-blocking)

## Verdict
APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION

$focus_prompt"
            ;;
    esac

    echo "$base_prompt"
}

# Main execution
main() {
    log_info "Starting Codex code review..."
    log_info "Review type: $REVIEW_TYPE"
    [[ -n "$FOCUS" ]] && log_info "Focus: $FOCUS"

    # Handle PR review - fetch diff first
    if [[ "$REVIEW_TYPE" == "pr" ]]; then
        if ! command -v gh &> /dev/null; then
            log_error "GitHub CLI (gh) is required for PR reviews"
            exit 1
        fi
        log_info "Fetching PR #$PR_NUMBER diff..."
        gh pr diff "$PR_NUMBER" > "/tmp/pr_${PR_NUMBER}_diff.txt"
    fi

    # Build command
    local cmd="codex exec"
    [[ -n "$MODEL" ]] && cmd="$cmd --model $MODEL"
    [[ -n "$OUTPUT_FILE" ]] && cmd="$cmd -o $OUTPUT_FILE"

    local prompt
    prompt=$(build_prompt)

    log_info "Running review..."
    echo ""

    # Execute codex
    eval "$cmd" "\"$prompt\""

    echo ""
    log_success "Review complete!"
    [[ -n "$OUTPUT_FILE" ]] && log_info "Output saved to: $OUTPUT_FILE"
}

main
