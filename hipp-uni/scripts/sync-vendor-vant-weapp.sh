#!/usr/bin/env bash
# 将 npm 包 @vant/weapp 的 miniprogram 产物同步到 wxcomponents（官方 lib，非自研）。
# 升级 @vant/weapp 版本后执行一次：bash scripts/sync-vendor-vant-weapp.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/node_modules/@vant/weapp/lib"
DST="$ROOT/static/wxcomponents/vant-weapp"
if [[ ! -d "$SRC" ]]; then
  echo "missing $SRC — run npm install in hipp-uni first" >&2
  exit 1
fi
rm -rf "$DST"
mkdir -p "$ROOT/static/wxcomponents"
cp -R "$SRC" "$DST"
echo "synced -> $DST"
