# Mercury 水星企业户 · 大陆用户操作手册

从公开帖子研究到可执行的 Wyoming 单成员 LLC、EIN、Mercury 企业户操作清单。

资料核验截至 **2026-10-23**；发布整理日期 **2026-10-24**。

[打开在线页面](https://siuserxiaowei.github.io/mercury-registration-guide/) · [飞书汇总文档](https://vi8r050ecuz.feishu.cn/docx/Tmcedh4VAoTMeaxmuqvcewxEnKY) · [发布信息](data/publication.json)

## 从这里开始

| 内容 | 入口 |
|---|---|
| 核心结论：企业户与个人户分别判断 | [阅读](content/conclusions.md) |
| 美国公司类型、注册州、完整流程与费用 | [阅读](content/full-process.md) |
| 大陆、无 SSN/ITIN、Wyoming 单成员 LLC 操作清单 | [阅读](content/checklist.md) |
| Mercury 业务说明英文模板 | [复制模板](content/business-template.txt) |
| 原始研究报告及证据限制 | [阅读](content/research.md) |
| 全部 142 条来源目录 | [阅读](content/catalogue.md) · [JSON](data/catalogue.json) · [TSV](data/catalogue.tsv) |
| 两年预算数据 | [JSON](data/budget.json) |

## 范围与证据

本轮公开检索执行 119 条查询，汇总 162 条观察，去重为 142 条目录记录。110 条记录经过原文复核，其中 22 条为弱证据；另有 4 条仅元数据复核、17 条受阻、11 条排除。可支持窄结论的原文强/中证据记录为 88 条。

这些是本次检索范围的目录与研究摘记，不是全网总量、热度排名或银行申请样本。核验帖主确实这样写过，不等于独立证明其银行审批事件；不能计算开户通过率。未知日期、商业推广、重复经历与证据限制均保留标记。

公司注册、EIN、账户批准和后续维护是不同环节。材料与模板要按真实业务填写；不承诺通过。第三方帖子与网站权利归原作者，本仓库保存元数据、研究分析和原文链接，不复制原帖全文。

## 本地构建

只需 Python 3。网页不使用外部 CDN、追踪器、第三方字体或账户材料收集。

```bash
python3 scripts/build_site.py
python3 -m http.server 8765 --directory docs
```

`content/` 为 Markdown 真源，`data/` 为公开研究数据，`dist/` 为静态构建结果，`docs/` 为 GitHub Pages 发布目录。修改后重新构建并提交，Pages 从 `main:/docs` 发布。

页面的待办状态和预算输入仅保存在访问者自己的浏览器，不接收护照、SSN、银行账户或申请文件。

