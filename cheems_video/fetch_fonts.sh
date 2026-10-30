#!/usr/bin/env bash
# 下载片中用到的开源字体（SIL OFL，来自 Google Fonts 仓库）
set -e
cd "$(dirname "$0")"
mkdir -p fonts
base=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sSfL -o fonts/ZCOOLKuaiLe-Regular.ttf "$base/zcoolkuaile/ZCOOLKuaiLe-Regular.ttf"
curl -sSfL -o fonts/ZCOOLQingKeHuangYou-Regular.ttf "$base/zcoolqingkehuangyou/ZCOOLQingKeHuangYou-Regular.ttf"
curl -sSfL -o fonts/MaShanZheng-Regular.ttf "$base/mashanzheng/MaShanZheng-Regular.ttf"
curl -sSfL -o fonts/LongCang-Regular.ttf "$base/longcang/LongCang-Regular.ttf"
curl -sSfL -o "fonts/NotoSansSC[wght].ttf" "$base/notosanssc/NotoSansSC%5Bwght%5D.ttf"
echo "字体已下载到 fonts/"
