# 第22章复现命令与结果回执审查（2026-09-02）

## 审查结论

- **内容准确性**：通过。正文区分命令 artifact 存在、进程成功退出、stdout digest 匹配和科学结果复现。
- **代码一致性**：通过。`EXP-22-01` v5 实际执行三个不经过 shell 的固定 `python3` probe，并保留 `reproduced`、`stdout_digest_mismatch`、`nonzero_exit` 三种状态。
- **追溯一致性**：通过。项目包的 authored receipt 绑定 reproduction command 与 result 的 URI/digest、exit code 和 stderr 字节数；第4/8/20/21章 trace revision 已同步为 v4/v4/v11/v11。
- **证据强度**：通过。stdout 只是固定字符串，receipt 未签名；没有遍历项目目录、重建环境、执行模型或独立 replication。

## 停止边界

只要 exit 非零或 stdout digest 不匹配，就不得把该运行记为 reproduced。即便本 fixture 通过，也只能说明受限子进程和字段绑定工作正常，不能提升为真实实验可复现或科学结论已验证。
