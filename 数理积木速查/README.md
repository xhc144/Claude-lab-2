# 数理积木速查

按“数学积木”格式（条件 → 具体操作/核心式 → 结果，红框只圈关键部分）整理的数学与物理速查，难度对标 MIT 本科高年级课程。
版式沿用用户样张《粒度与重点样张》：ctexart + 蓝色结论框 + 红色局部重点框。

- `main.tex`：主文件；`chapters/`：各章（`01-…` 为原稿，`01b`、`01c`… 为续写）。
- `核验/`：符号与数值核验脚本（sympy、numpy、scipy、mpmath）和结果 JSON，说明见 `核验/核验记录.md`。
- `数理积木速查.pdf`：编译好的成品。

## 重新生成

```sh
xelatex main.tex && xelatex main.tex      # 两遍生成目录
cd 核验 && python3 verify_math4.py        # 任一核验脚本
```
