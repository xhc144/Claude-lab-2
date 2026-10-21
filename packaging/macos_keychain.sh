#!/bin/bash
# 把 Developer ID 证书导入临时钥匙串，并把签名身份写入 $GITHUB_ENV 供 build.py 使用。
# 需要的环境变量（GitHub Secrets）：MACOS_CERT_P12（.p12 的 Base64）、MACOS_CERT_PASSWORD
set -euo pipefail
KEYCHAIN="$RUNNER_TEMP/folio-signing.keychain-db"
KC_PASS="$(uuidgen)"
P12="$RUNNER_TEMP/folio-cert.p12"
echo "$MACOS_CERT_P12" | base64 --decode > "$P12"
security create-keychain -p "$KC_PASS" "$KEYCHAIN"
security set-keychain-settings -lut 21600 "$KEYCHAIN"
security unlock-keychain -p "$KC_PASS" "$KEYCHAIN"
security import "$P12" -P "$MACOS_CERT_PASSWORD" -A -t cert -f pkcs12 -k "$KEYCHAIN"
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KC_PASS" "$KEYCHAIN" > /dev/null
security list-keychains -d user -s "$KEYCHAIN" $(security list-keychains -d user | tr -d '"')
rm -f "$P12"
IDENTITY="$(security find-identity -v -p codesigning "$KEYCHAIN" | grep -m1 'Developer ID Application' | sed -E 's/.*"(.+)"/\1/')"
if [ -z "$IDENTITY" ]; then
  echo "证书里没有找到 Developer ID Application 身份" >&2
  exit 1
fi
echo "签名身份：$IDENTITY"
echo "MACOS_SIGN_IDENTITY=$IDENTITY" >> "$GITHUB_ENV"
