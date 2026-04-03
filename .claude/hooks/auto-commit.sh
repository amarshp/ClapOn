#!/usr/bin/env bash
# auto-commit.sh — Safe structured auto-commit for ClapOn
# Called by Claude Code's Stop hook after each session turn.

# Find repo root regardless of CWD
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$REPO" || exit 0

# ── 1. Branch isolation ────────────────────────────────────────────────────────
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
if [ "$current_branch" != "claude-auto" ]; then
    # Create branch if it doesn't exist, otherwise just switch
    git checkout -b claude-auto 2>/dev/null || git checkout claude-auto 2>/dev/null || true
fi

# ── 2. Scoped staging (never git add -A) ──────────────────────────────────────
# Add known source directories and config files if they exist
for target in src tests config.toml pyproject.toml .gitignore; do
    [ -e "$target" ] && git add -- "$target" 2>/dev/null || true
done

# Add root-level .py files (check.py, test_*.py, etc.)
find . -maxdepth 1 -name "*.py" -print0 2>/dev/null | xargs -0 -r git add -- 2>/dev/null || true

# ── 3. Exit silently if nothing staged ────────────────────────────────────────
git diff --cached --quiet && exit 0

# ── 4. Safety check: run pytest if tests/ exists ──────────────────────────────
if [ -d "tests" ]; then
    pytest_exit=0
    python -m pytest tests/ -q --tb=no --no-header 2>/dev/null || pytest_exit=$?
    # Exit code 5 = no tests collected (safe to commit)
    # Exit code 0 = all tests passed (safe to commit)
    # Anything else = test failure (block commit)
    if [ "$pytest_exit" -ne 0 ] && [ "$pytest_exit" -ne 5 ]; then
        echo "[auto-commit] Tests failed (exit $pytest_exit) – skipping commit" >&2
        git reset HEAD -- . 2>/dev/null || true
        exit 0
    fi
fi

# ── 5. Build descriptive commit message ───────────────────────────────────────
file_list=$(git diff --cached --name-only 2>/dev/null)
count=$(echo "$file_list" | wc -l | tr -d ' ')
summary=$(echo "$file_list" | head -3 | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')
[ "$count" -gt 3 ] && summary="${summary} (+$((count - 3)) more)"

# ── 6. Commit ─────────────────────────────────────────────────────────────────
git commit -m "claude: update ${summary}" 2>/dev/null || true
