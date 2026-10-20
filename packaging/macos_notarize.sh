#!/bin/bash
# 把已签名的 .app 提交给 Apple 公证，并把公证票据钉到 .app 上。
# 需要的环境变量（GitHub Secrets）：APPLE_ID、APPLE_TEAM_ID、APPLE_APP_PASSWORD（App 专用密码）
set -euo pipefail
APP="$1"
codesign --verify --deep --strict --verbose=2 "$APP"
ZIP="$RUNNER_TEMP/folio-notarize.zip"
ditto -c -k --keepParent "$APP" "$ZIP"
xcrun notarytool submit "$ZIP" --apple-id "$APPLE_ID" --team-id "$APPLE_TEAM_ID" --password "$APPLE_APP_PASSWORD" --wait
xcrun stapler staple "$APP"
spctl --assess --type execute --verbose "$APP"
rm -f "$ZIP"
