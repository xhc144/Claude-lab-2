# 分支历史与恢复入口（2026-10-30）

仓库：`xhc144/Claude-lab-2`。这次把所有分支合并进 `main`，然后只保留 `main`。合并用的是普通合并提交（`--no-ff`），没有强推、改写历史、创建标签或触发手动发布。

| 删除的分支 | 合并时的完整 tip SHA | 内容 |
| --- | --- | --- |
| `claude/eloquent-bohr-vzee65` | `0ae2c3a53f163290394d2cd5726a0e39ce1f7808` | CI：自动更新测试单独一步运行（PR #3 合并之后补的一个提交） |
| `claude/compassionate-mendel-b6inxy` | `0493cca056a55c64c81bd6702694027c2d0b8c31` | `cheems_video/`：Cheems 规则怪谈动画短片的生成代码 |
| `claude/festive-clarke-ow6ff4` | `4c79c1b74013b444a3279a7c988ee91ae150835a` | `statistics_notes/`：数理统计自学讲义（重构版） |
| `claude/geo-topo-video` | `abfff463bdca618223fa80914eaa5da0c5e3b7d3` | `geo-topo-video/`：几何与拓扑五道经典难题（PR #5） |
| `claude/knot-theory-video` | `1a012c048126188dcf50f90b823e624d9179eb51` | `knot-theory-video/`：扭结理论速通（PR #6） |
| `claude/upbeat-planck-mk47d1` | `71e7d6836e976434cad07175d5f598f19ac86552` | `langlands-video/`：朗兰兹纲领介绍视频 |
| `claude/split-shell-menu` | `da92aedb96b7fb12dfdd4dd9149b4c616ec6322a` | 早已经由 PR #4 合并，只删分支名 |
| `claude/gifted-babbage-x0nnh5` | （本次工作分支，合并后删除） | `probability-distributions-video/`、仓库定义改动和上面各分支的合并提交 |

合并前 `main` 的 tip 是 `27fced9c2c2569331eecca15e418a3aedd5870c1`。

以上提交都在 `main` 的祖先历史里，删除分支名不会删除它们。需要回看某个分支时，在本地克隆里用完整 SHA：

```bash
git show 1a012c048126188dcf50f90b823e624d9179eb51
git switch -c recovered/knot-theory-video 1a012c048126188dcf50f90b823e624d9179eb51
```

上一次整理的记录见 [BRANCH-RECOVERY-20261021.md](BRANCH-RECOVERY-20261021.md)。
