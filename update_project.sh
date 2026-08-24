#!/usr/bin/env bash

set -Eeuo pipefail

skip_checks=false

usage() {
    cat <<'EOF'
Usage: bash ./update_project.sh [--skip-checks]

Updates the current Git branch with fast-forward only, synchronizes the uv
environment from uv.lock, and runs Ruff plus pytest.

Options:
  --skip-checks  Update code and dependencies without Ruff or pytest.
  -h, --help     Show this help.
EOF
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

run() {
    printf '\n> '
    printf '%q ' "$@"
    printf '\n'
    "$@"
}

require_command() {
    command -v "$1" >/dev/null 2>&1 ||
        die "Required command '$1' was not found in PATH. See WINDOWS_SETUP.md."
}

while (($# > 0)); do
    case "$1" in
        --skip-checks)
            skip_checks=true
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            die "Unknown argument: $1"
            ;;
    esac
    shift
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

printf 'WPI project update\n'
printf 'Project directory: %s\n' "$script_dir"

require_command git
require_command uv

[[ -d .git ]] || die "This directory is not a Git clone: $script_dir"
[[ -f pyproject.toml ]] || die "pyproject.toml was not found in $script_dir"
[[ -f uv.lock ]] || die "uv.lock was not found in $script_dir"

branch="$(git branch --show-current)"
[[ -n "$branch" ]] ||
    die 'Detached HEAD is not supported. Switch to a branch before updating.'
printf 'Current branch: %s\n' "$branch"

changes="$(git status --porcelain)"
if [[ -n "$changes" ]]; then
    printf '\nLocal changes:\n%s\n' "$changes" >&2
    die 'The working tree is not clean. Commit or otherwise save local changes first.'
fi

upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)" ||
    die "Branch '$branch' has no upstream. Configure it before updating."
printf 'Upstream branch: %s\n' "$upstream"

run git fetch --all --prune
run git merge --ff-only "$upstream"
run uv sync --frozen --group dev

if [[ "$skip_checks" == false ]]; then
    run uv run ruff check .
    run uv run pytest -q
else
    printf '\nChecks were skipped by request.\n'
fi

printf '\nUpdate completed successfully.\n'
printf 'Start the application with: uv run python main.py\n'
