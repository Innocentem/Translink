#!/bin/bash

# Ensure a commit message is provided
if [ -z "$1" ]; then
  echo "Usage: $0 \"commit message\" [--push]"
  exit 1
fi

COMMIT_MESSAGE="$1"
PUSH=false  # Default: Do not push

# Check if --push flag is present
if [[ "$" == *"--push" ]]; then
  PUSH=true
fi

# Add all changes
git add .

# Commit with the provided message
git commit -m "$COMMIT_MESSAGE"

# Push only if --push flag is passed
if $PUSH; then
  git push
  echo "Changes pushed to remote repository."
else
  echo "Commit created but not pushed (use --push to push changes)."
fi