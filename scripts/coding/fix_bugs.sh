#!/bin/bash

# 1. Choose your tool
TOOL="codex" 

# 2. Safety Check: Ensure the user knows about Git Clean
echo "⚠️  WARNING: This script will 'git checkout' failing fixes."
echo "Ensure you have run 'git add .' to protect your new files!"

# 3. Use a more robust loop for the files
for issue_file in bugs/00[0-9]_issue.md; do
  [ -e "$issue_file" ] || continue # Skip if no files match
  
  echo "================================================"
  echo "🚀 TOOL: $TOOL  |  TASK: $issue_file"
  echo "================================================"

  PROMPT="Fix the bug in $issue_file. Create a test. Run ./smoke-test.sh. Update docs. Stop."

  # Setup Tool Paths
  case $TOOL in
    claude) CMD="claude -p '$PROMPT' --dangerously-skip-permissions"; AUTH="$HOME/.claude:/home/developer/.claude" ;;
    gemini) CMD="gemini -p '$PROMPT' --yolo"; AUTH="$HOME/.gemini:/home/developer/.gemini" ;;
    codex)  CMD="codex '$PROMPT' --yolo"; AUTH="$HOME/.codex:/home/developer/.codex" ;;
  esac

  # 4. The Corrected Docker Run
  # --user: Fixes the 'Permission Denied'
  # --network host: Fixes the 'API unreachable'
  docker run --rm \
    --user $(id -u):$(id -g) \
    --network host \
    -v "$(pwd)":/app \
    -v "$AUTH" \
    --workdir /app \
    ai-sandbox \
    "$CMD"

  # 5. Safer Verification
  if ./scripts/api/smoke-test.sh; then
    echo "✅ Success for $issue_file"
  else
    echo "❌ AI failed. Reverting code changes (keeping your scripts)."
    git checkout . 
    # Removed 'git clean -fd' to prevent accidental deletion of your work
  fi
done