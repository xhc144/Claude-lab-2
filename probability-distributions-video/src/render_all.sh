#!/bin/bash
# 渲染全部场景（1080p60，4 个并行）。每个场景用单独的 media 目录，避免并行编译 LaTeX 时互相覆盖。
# 用法：./render_all.sh [画质参数，默认 -qh] [场景...]
cd "$(dirname "$0")"
Q=${1:--qh}
shift
LIST=${*:-"S02 S05 S04 S01 S08 S06 S03 S07 S09 S00"}
declare -A FILE=([S00]=scenes_a [S01]=scenes_a [S02]=scenes_b [S03]=scenes_b [S04]=scenes_c [S05]=scenes_c
                 [S06]=scenes_d [S07]=scenes_d [S08]=scenes_e [S09]=scenes_e)
mkdir -p logs
for s in $LIST; do echo "$s ${FILE[$s]}"; done | xargs -P 4 -n 2 sh -c \
  'manim '"$Q"' --disable_caching --media_dir media/$0 $1.py $0 > logs/$0.log 2>&1 && echo "$0 完成" || echo "$0 失败"'
