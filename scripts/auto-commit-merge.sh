#!/usr/bin/env bash
set -euo pipefail

LOGFILE=".git/auto-commit-merge.log"
INTERVAL_SEC=$((5 * 60))
UPSTREAM="origin/main"

log() {
  printf '%s %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*" | tee -a "$LOGFILE"
}

count_unique() {
  # print unique line count from stdin
  awk '!seen[$0]++' | wc -l | tr -d ' '
}

commit_if_needed() {
  # Detect staged and unstaged tracked changes
  local staged unstaged n_files
  staged=$(git diff --name-only --cached)
  unstaged=$(git diff --name-only)
  n_files=$(printf "%s\n%s\n" "$staged" "$unstaged" | grep -v '^$' | count_unique)

  if [ "$n_files" -eq 0 ]; then
    return 0
  fi

  if [ -n "$staged" ]; then
    # Respect user staging if present
    git commit -m "chore(auto): save (${n_files} files)" 2>>"$LOGFILE" \
      && log "Committed staged changes (${n_files} files)" \
      || { log "Commit failed (staged). Preserving state; skipping this cycle"; return 0; }
  else
    # Tracked files + ensure .windsurf changes are included
    git add -u && git add .windsurf 2>/dev/null || true
    if ! git diff --cached --quiet; then
      git commit -m "chore(auto): save (${n_files} files)" 2>>"$LOGFILE" \
        && log "Committed changes (${n_files} files, incl. .windsurf)" \
        || { log "Commit failed. Preserving state; skipping this cycle"; return 0; }
    fi
  fi
}

merge_upstream() {
  # Fetch and attempt merge of origin/main
  git fetch origin >>"$LOGFILE" 2>&1 || { log "Fetch failed"; return 1; }

  # Fast-forward or merge with no edit; stop on conflicts
  if git merge --no-edit "$UPSTREAM" >>"$LOGFILE" 2>&1; then
    log "Merged $UPSTREAM successfully"
    return 0
  else
    log "Merge produced conflicts; aborting merge to keep repo clean"
    git merge --abort >>"$LOGFILE" 2>&1 || true
    echo "conflict" > .git/auto-commit-merge.conflict
    return 2
  fi
}

main_loop() {
  log "Auto commit/merge loop started. Interval=${INTERVAL_SEC}s, upstream=$UPSTREAM"
  while true; do
    # Ensure we are inside a git repo
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
      log "Not a git repo; exiting"
      exit 1
    fi

    # Commit changes if any
    commit_if_needed || true

    # Merge upstream
    merge_upstream || true

    sleep "$INTERVAL_SEC"
  done
}

main_loop
