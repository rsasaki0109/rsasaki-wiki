#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_DEST="${HOME}/ドキュメント/Obsidian Vault/rsasaki-hub"
DEST="${1:-${DEFAULT_DEST}}"

mkdir -p "${DEST}"

rsync -a --delete --prune-empty-dirs \
  --exclude '.cache/' \
  --exclude '.git/' \
  --exclude '.obsidian/' \
  --include '*/' \
  --include '*.md' \
  --exclude '*' \
  "${REPO_ROOT}/" "${DEST}/"

count="$(find "${DEST}" -name '*.md' | wc -l | tr -d '[:space:]')"
printf 'Markdown ファイル %s 件を %s へ同期しました\n' "${count}" "${DEST}"
