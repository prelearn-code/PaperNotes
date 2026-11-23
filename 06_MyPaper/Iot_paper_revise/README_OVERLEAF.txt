IoT Audit / ARC-Audit - Overleaf source package

英文独立主稿使用 main.tex 和 pdfLaTeX。导入 Overleaf 时，将 main.tex、
IEEEtran.cls、IEEEtran.bst、IEEEabrv.bib、bstcontrol.bib、references.bib 和
正文引用的 figures/ 文件按原目录结构打包，再选择 New Project → Upload Project。
中文独立主稿使用 main_cn.tex 和 XeLaTeX，打包时选用中文主文件及其引用的插图。
中文稿指定 Windows 中文字体，在线编译时需在上传副本中配置可用的对应字体。

当前目录保存论文、排版表格、插图及绘图源行。原始观测、配置和源码快照位于本工作区的独立归档。

归档标识
  dual_hai_20261008_v3
  C1: reduced；C2/C3 与机制对照: full
  归档位置（相对于本目录）:
  ../Iot_Audit/ARC-Audit_Overleaf_Latest_Miao_20260930_222314/evidence/current-secure/
  CONTRIBUTION_SOURCES.json 的 SHA-256:
  b453e50aa1dd8a6cbccb9f89160cc2e5ae691a5705a44ce565ab69381c900c67
  config/full/run_manifest.json 的 SHA-256:
  d1a5c4886491ff067c4210e3a9e23326fcdfe06bf4443428a29121342987f6c2
  config/reduced/run_manifest.json 的 SHA-256:
  6d8c77aa9aedb47289ab87eb58988ad10e0503ccefde96e4df5f07236d3f3fbe

从归档根目录核验论文汇总值:
  python verify_current_evidence.py

逐案核对:
  results/C1_observations.csv、C2_observations.csv、C3_observations.csv
  位于归档 results/ 下。C2 表示机制对照取 mechanism_controls.csv 中
  kind=representation-audit 的四条记录。正文 C3 配对表按数据段、布局、
  擦除率、案例、批次和目标对齐记录，每个布局及擦除率各有 50 个匹配案例。

本地复跑:
  WSL 项目 /home/zsw/codes/Paper/Exp/Iot_Audit_MY 的冻结结果位于
  results/route_a_secure/dual_hai_20261008_v3。
  正式复跑应使用归档源码快照及匹配输入，避免覆盖冻结结果。将两个原始 CSV
  置于快照根目录的 database/hai21_raw/（train1.csv 和 train2.csv），并依据
  对应 run_manifest.json 核验输入哈希、源码和依赖版本。复跑入口位于
  source_snapshot/sandbox/route_a_secure/experiment.py。
  在配置好快照依赖的环境中，从 source_snapshot/ 运行:
    python sandbox/route_a_secure/experiment.py --profile full --preflight --out /tmp/arc-audit-full-check
  正式运行时移除 --preflight，并指定独立输出目录。C1 使用 --profile reduced。
  当前稿新增的 C3 配对表来自归档观测，耗时仍为原始运行中的实测值。
