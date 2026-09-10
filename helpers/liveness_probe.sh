#!/bin/sh
REPO="${REPO_DIR:-/content}"
BRANCH="${GIT_BRANCH:-main}"

local_sha=$(git -C "$REPO" rev-parse HEAD 2>/dev/null) || { echo "not a git repo: $REPO"; exit 1; }
remote_sha=$(GIT_TERMINAL_PROMPT=0 timeout 10 git -C "$REPO" ls-remote origin "refs/heads/$BRANCH" 2>/dev/null | cut -f1)

if [ -z "$remote_sha" ]; then
  echo "unable to fetch due to branch not found or repo"
elif [ "$remote_sha" = "$local_sha" ]; then
  echo "up to date"
else
  echo "stale: local=$local_sha remote=$remote_sha"
  exit 1
fi

