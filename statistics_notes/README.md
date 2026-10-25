# 数理统计自学讲义（重构版）

在原《新领军计划数理统计自学讲义》（仓库根目录的 `statistics_teacher_JX28.pdf`）基础上，
结合对它的批评意见重新组织、重新写作的自学讲义。成品是 `数理统计自学讲义_重构版.pdf`（89 页）。

## 结构

| 章 | 内容 |
|---|---|
| 第 0 章 概率工具箱 | 协方差与和的方差、切比雪夫、两种收敛、中心极限定理、Slutsky、Delta 方法（原讲义缺的前置知识） |
| 第 1 章 数据与抽样 | 描述统计与箱线图、抽样分布、标准误、样本方差、不放回抽样、分层与 Neyman 分配 |
| 第 2 章 估计量及其误差 | 偏差、方差、均方误差、无偏性的局限、逆方差加权、相合性 |
| 第 3 章 矩估计与极大似然 | 可识别性、似然、MLE、Fisher 信息、Cramér–Rao 下界、截尾数据 |
| 第 4 章 置信区间与假设检验 | t 分布推导、Wilson 区间、功效与样本量、p 值的误读、检验与区间的对偶 |
| 第 5 章 两个样本的比较 | 配对、合并方差 t、Welch 检验（含模拟比较）、两比例、置换检验、QQ 图与敏感性分析 |
| 第 6 章 一元线性回归 | 最小二乘与投影、推断、置信带与预测带、残差图、杠杆与影响、Forbes 完整案例 |
| 附录 | 全部 67 道习题解答（A 基础 / B 进阶 / C 挑战）、分位数表、原讲义内容的去向 |

真实数据：Student（1908）睡眠药物数据、Forbes（1857）沸点与气压数据，计算结果已与文献值核对。

## 编译

需要 XeLaTeX（ctex、tcolorbox、pgfplots）和字体 TeX Gyre Pagella / Pagella Math、Noto Serif/Sans CJK SC、LXGW WenKai。

```sh
python tools/make_figdata.py      # 重新生成 figdata/（需要 numpy、scipy；模拟均固定随机种子）
latexmk -xelatex main.tex
```
