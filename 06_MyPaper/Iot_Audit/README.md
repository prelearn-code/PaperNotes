# IoT Audit 文档入口

当前论文版本更新于 **2026-10-09 晚间**。项目目录沿用原名称 `ARC-Audit_Overleaf_Latest_Miao_20260930_222314`，其中包含最新文件。

后续保护分配实验已推进到 **2026-10-22 的 Plan65**，尚未合入论文主稿。请先读 [当前创新点与实验效果总结](ARC_Audit_当前创新点与实验效果总结_20261027.md)，再看 [Plan65 详细报告](ARC_Audit_Plan65_Joint_20261022.md)。

三项论文贡献的实验设计、完成状态、详细结果和本地文献见 [C1/C2/C3 实验与文献总结](ARC_Audit_三项贡献实验配置结果与本地文献_20261027.md)。

新提出的双 CSV 跨文件方案的设计核对见[可行性与代码修改评估](ARC_Audit_双CSV方案可行性与代码修改评估_20261028.md)。

C1 已完成独立代码适配及小规模带标签检查，见 [C1 代码与结果说明](ARC_Audit_C1代码适配与小规模检查_20261028.md)。源码仅在 WSL `/home/zsw/codes/Paper/Exp/Iot_Audit_MY/sandbox/route_a_crossfile_v1/`，后续实验代码也直接在 WSL 项目修改。双 CSV 全量正式实验及新 C2/C3 尚未完成。

- [英文论文 PDF](ARC-Audit_Overleaf_Latest_Miao_20260930_222314/main.pdf) · [LaTeX 源码](ARC-Audit_Overleaf_Latest_Miao_20260930_222314/main.tex)
- [中文论文 PDF](ARC-Audit_Overleaf_Latest_Miao_20260930_222314/main_cn.pdf) · [LaTeX 源码](ARC-Audit_Overleaf_Latest_Miao_20260930_222314/main_cn.tex)
- [补充材料 PDF](ARC-Audit_Overleaf_Latest_Miao_20260930_222314/supplementary.pdf) · [LaTeX 源码](ARC-Audit_Overleaf_Latest_Miao_20260930_222314/supplementary.tex)
- 实验包 `paper_C1_reduced_C2C3_full_20261009.zip` 保存在本地。C1 为两个 21,600 行窗口，C2/C3 为完整数据段。
- [当前论文逐节修订计划](ARC_Audit_Revision_Plan_20261009_C2C3Full.md)

当前论文的实验观测和汇总表位于项目内的 `evidence/current-secure/`。源码快照和 Python 脚本保存在本地，实验代码在 WSL 项目 `/home/zsw/codes/Paper/Exp/Iot_Audit_MY` 维护。编译说明见 [README_OVERLEAF.txt](ARC-Audit_Overleaf_Latest_Miao_20260930_222314/README_OVERLEAF.txt)。

`reference/` 保留参考文献 PDF，`数据集评估/` 保留原始数据与数据概况。

2026-10-21 已清理旧稿、旧实验包、历史审阅与实验快照、旧图及编译临时文件。
