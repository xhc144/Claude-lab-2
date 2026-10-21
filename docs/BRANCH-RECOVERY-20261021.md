# 分支历史与恢复入口（2026-10-21）

仓库：`xhc144/Claude-lab-2`。默认分支为 `main`。本次只用正常快进保留原提交；没有强推、创建标签、触发手动发布或改变仓库设置。

| 原分支或基线 | 保留的完整 tip SHA | 说明 |
| --- | --- | --- |
| `main` 合入前 | `21f7ebafe076db99ba4396b37897b21662001d40` | 原已合入安装器的基线 |
| `claude/windows-installer` | `fb0e38514b96b403d6d9d40c06d30cb7462e9dfd` | 其全部提交已经包含在原 main；此前已清理分支名 |
| `claude/wizardly-thompson-0jg375` | `17d3ead4715cde721cc0e63a46afa16147585a88` | 0.2.2 功能与 CI 修复，合入前关联两次 CI 均成功 |

以上原提交仍在 main 的祖先历史中。分支名删除不会删除这些历史文件。需要回看时，可在已授权的本地克隆中使用完整 SHA：

```bash
git show 17d3ead4715cde721cc0e63a46afa16147585a88
git switch -c recovered/folio-0.2.2 17d3ead4715cde721cc0e63a46afa16147585a88
```

这只是本地恢复示例，不要求重新创建远端副分支。原 tip 另有完整 Git bundle 独立恢复和 fsck 验证；main 历史本身也完整保留原提交。

合入前源 tip 的验证：[push CI 39536110471](https://github.com/xhc144/Claude-lab-2/actions/runs/39536110471)、[原作者手动运行 39536116659](https://github.com/xhc144/Claude-lab-2/actions/runs/39536116659) 均成功。这两次运行属于原分支制作过程，本次整理没有调用手动发布。

发布条件已核对：正式 release 仅在推送 `v*` 标签，或手动运行且填写 `release` 输入时执行。普通 `refs/heads/main` push 不满足此条件；本次合入只触发测试与打包，正式发布步骤应跳过。合入后的真实 CI 结果记录在分支整理交接报告中，不用本说明自引用后续提交。
