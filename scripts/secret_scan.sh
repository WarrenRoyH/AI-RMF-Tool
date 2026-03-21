#!/bin/bash
# AI-RMF Secret Scanner: Checks git diff for sensitive patterns before commit.

# 1. Define common secret patterns
PATTERNS=(
  "GOOGLE_API_KEY"
  "AI_RMF_MODEL"
  "BEGIN RSA PRIVATE KEY"
  "BEGIN OPENSSH PRIVATE KEY"
  "AI_KEY"
  "SECRET_KEY"
  "PASSWORD"
  "https://[^:]+:[^@]+@github.com" # Basic check for credentials in URLs
)

echo "--- [SECRET SCAN]: Analyzing staged changes... ---"

# 2. Get the current staged diff
DIFF=$(git diff --staged)

if [ -z "$DIFF" ]; then
  echo "[OK]: No staged changes to scan."
  exit 0
fi

# 3. Check for each pattern in the diff
FOUND_SECRETS=0
for pattern in "${PATTERNS[@]}"; do
  # Search the diff for the pattern, but only in lines starting with '+'
  if echo "$DIFF" | grep -E "^\+.*$pattern" > /dev/null; then
    echo "[!] CRITICAL: Found sensitive pattern '$pattern' in staged changes!"
    FOUND_SECRETS=$((FOUND_SECRETS + 1))
  fi
done

# 4. Exit based on findings
if [ "$FOUND_SECRETS" -gt 0 ]; then
  echo "--- [SECRET SCAN]: FAILED ($FOUND_SECRETS secrets found) ---"
  echo "--- ACTION: Please remove secrets from your code before committing. ---"
  exit 1
else
  echo "--- [SECRET SCAN]: PASSED (No common secrets found) ---"
  exit 0
fi
