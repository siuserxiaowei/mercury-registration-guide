#!/usr/bin/env python3
"""Export the reviewed public research into a minimal publishing bundle.

Source packages are read only. No credentials, private application documents,
worker artifacts or local paths are included in the exported catalogue.
"""
import argparse
import collections
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESEARCH = None
CHECKLIST = None
META = '发布：2026-10-24。资料核验截至：2026-10-23。金额均为美元（USD）；费用、规则与处理进度可能变化，提交前复核所附官方入口。\n\n'

CONCLUSIONS = r'''# 大陆用户申请 Mercury：企业户与个人户核心结论

大陆居民可以为符合条件的美国公司申请 Mercury 企业户；个人户需要美国居住条件和有效 SSN，不能仅靠中国护照、ITIN 或美国公司申请。Mercury 是金融科技平台，银行服务由其合作银行提供；本文沿用中文讨论中的“水星银行”称呼。

## 企业户：大陆用户可以申请，但美国公司只是第一步

公司须在美国或美国属地注册，并有现有或计划中的美国业务。创始人不必是美国公民或居民。核验时中国大陆不在官方禁止居住地区名单中，但符合资格不代表一定获批。[企业户资格](https://support.mercury.com/hc/en-us/articles/28770467511060-Eligibility-and-requirements-for-opening-a-Mercury-account)、[禁止地区名单](https://support.mercury.com/hc/en-us/articles/28771710754580-Prohibited-countries)

| 材料 | 准备方式 |
|---|---|
| 美国公司成立文件 | 州政府备案的 Articles of Organization、Articles of Incorporation、Certificate of Formation 等 |
| IRS 签发的 EIN 证明 | CP575、147C、IRS 返回的 SS-4，或官方接受的 IRS 在线确认截图；自行填写、未经 IRS 处理的 SS-4 不能冒充 IRS-issued 证明 |
| 所有权与身份证明 | 直接或间接持股 ≥25% 的自然人，以及至少一名实际管理负责人；国际申请人准备有效护照 |
| 业务资料 | 如实说明产品或服务、客户、资金来源、现有或计划中的美国业务 |
| 地址证明，按要求补交 | 显示公司或受益所有人姓名及完整地址的账单、租约等；银行或信用卡账单通常要求最近90天 |

重要补充：Mercury 主站 FAQ 允许 EIN 待批时凭完整 SS-4 申请，并在获批后90天内补正式 EIN；帮助中心材料清单仍强调 IRS-issued 证明。本指南选择先取得正式证明再申请的主路线，不能理解成待批 EIN 绝对无法提交，也不保证例外路线必获受理。[官方 FAQ](https://mercury.com/faq)、[文件清单](https://support.mercury.com/hc/en-us/articles/28770957425172-Gathering-your-documents)

### 四类地址必须分开

| 地址 | 大陆申请人应如何处理 |
|---|---|
| 公司法定地址 Legal address | 满足 Mercury 美国实体地址要求，不得是 PO Box 或虚拟办公室；商家赠送地址须核实属性和用途 |
| 实际经营地址 Physical address | 日常真正工作的地方，可以是中国大陆真实住宅；不能用注册代理、虚拟邮箱或收信中心替代 |
| 股东居住地址 Residential address | 每位受益所有人真实当前住址，不能拿公司代理地址替代 |
| 收件地址 Mailing address | 按可投递要求用于寄卡；可收件不等于可证明实际经营或居住 |

不必一概租美国办公室，也不能认为购买美国虚拟地址就够。[公司地址规则](https://support.mercury.com/hc/en-us/articles/28769699533588-Company-address-requirements)、[法定地址要求](https://support.mercury.com/hc/en-us/articles/28769816280084-Updating-your-company-s-legal-address)

### 申请步骤

1. 先确认真实业务和美国业务联系，再设立合适的美国主体；仅有中国大陆公司不满足当前企业户主体要求。
2. 取得公司成立文件和 EIN，按真实情况整理股权及负责人信息。
3. 备齐护照、真实住址和备用地址证明，核对姓名、地址、公司名称能够相互对应。
4. 写清产品或服务、美国客户/供应商/计划及资金来源；合同、订单和发票只提交真实存在的材料。
5. 从 [Mercury 官网企业入口](https://mercury.com/business-banking)填写公司、行业、地址、所有权等信息并完成验证。
6. 提交后确认 In Review，查收邮箱和垃圾邮件，按要求补件。官方称通常0–2个工作日决定；补件可能延长，外部银行关联是可选步骤。[提交后流程](https://support.mercury.com/hc/en-us/articles/28771494745364-What-happens-after-I-submit-my-Mercury-business-account-application)
7. 获批后启用双重验证，按真实业务收付款，保存合同、票据、流水和股东出资记录。

美国业务联系可能开户后继续核验。没有美国业务、无计划或无法提供合格证明，账户可能被限制或关闭。[美国业务核验](https://support.mercury.com/hc/en-us/articles/53171397356820-Verifying-your-U-S-business-operations)

### 容易出问题的地方

- 资格不符：主体不合格、没有美国业务或计划，或涉及禁止地区和行业。
- 地址不合格：把注册代理、虚拟邮箱填作实际经营地或股东住址；地址无法核实。
- 文件不完整或不一致：EIN 证明类型错误、证件不清晰、姓名/公司名不能对应、缺少门牌或单元号。
- 业务无法核验：填写的业务、网站、合同、预期交易和资金来源互相矛盾。网站不是统一硬门槛，提供的网站应对应申请主体和业务。[官方申请提示](https://support.mercury.com/hc/en-us/articles/35621290252052-Application-tips)

这些是依据规则应优先检查的事项，不能反推出某位帖主一定因此被拒。美国IP、Atlas、某个州、LLC或INC、推荐链接均没有可靠的必过保证。

### 帖子给出的实际信号

- [Meepo](https://meepo.me/mercury-bank-approved)自述使用中国真实住宅地址及招商银行中文账单获批。
- [rokcso](https://rokcso.com/p/mercury-business-account-application)自述使用中文信用卡账单、经过两次补件后获批；文中含商业推荐链接。
- [V2EX 同一讨论](https://www.v2ex.com/t/1200890)既有大陆护照、LLC、EIN 齐备仍多次被拒的自述，也有使用国内真实地址获批的评论自述。

上述都是作者或评论者自述，原文核对不等于独立核实银行账户或全部申请材料，不能计算总体通过率。中文材料若需翻译，应按审核要求处理，不能自行改动原始账单。Meepo博客和同作者V2EX记录属于同一经历链，不能当成两个独立成功申请人。

被拒后，官方允许有新增信息或材料时重新申请，但不保证批准，也通常不披露具体拒绝原因。先修正材料缺口，再从原申请账户处理；换邮箱或改写行业不能替代真实新增证据。[重新申请说明](https://support.mercury.com/hc/en-us/articles/31759083693844-Reapplying-if-your-Mercury-application-has-been-denied)

## 个人户：普通常住大陆用户通常不具备条件

Mercury Personal 要求年满18岁，并同时具备有效美国 SSN（明确不接受 ITIN）、真实美国住宅地址、美国手机号、政府签发照片身份证件；不接受 PO Box 或虚拟邮箱替代住宅地址。[个人户条件](https://support.mercury.com/hc/en-us/articles/30467047130516-Eligibility-for-Mercury-Personal)

| 已有条件 | 能否据此直接申请个人户 |
|---|---|
| 中国护照和大陆住址 | 不足，仍需满足全部 Personal 条件 |
| ITIN和美国收信地址 | 不足；ITIN不替代SSN，收信地址不替代住宅地址 |
| 美国LLC和EIN | 公司材料不能替代个人户条件 |
| 已获批Mercury企业户 | 不自动取得个人户资格，仍须单独审核 |

中国国籍本身不能与是否具备申请资格画等号；满足全部实际条件的申请人仍以审核为准。企业户可能带来的个人户费用优惠不会改变资格。[企业户与个人户](https://support.mercury.com/hc/en-us/articles/46142613128852-Waiving-your-Mercury-Personal-subscription-fee-as-a-Business-customer)

确实满足条件时，从 [Personal 官方入口](https://mercury.com/personal-banking)填写身份、SSN、真实美国住宅地址和手机号，上传照片证件并完成验证。已有企业户可从公司名称下的 Apply for a new account → Mercury Personal 进入。

这批帖子没有提供足以证明“常住大陆、没有美国居住条件也可凭企业户绕过 Personal 要求”的可靠案例。不要仅为个人消费账户而盲目购买公司注册服务。
'''

FULL_PROCESS = r'''# 大陆用户从美国公司、EIN 到 Mercury 企业户的完整流程

路线：确定真实业务 → 选公司类型和州 → 注册公司 → 取得 EIN → 申请 Mercury 企业户 → 持续记账、申报和维护。

对人在大陆、无美国实体团队、暂无机构融资的一人业务，可优先评估 Wyoming 单成员 LLC；明确准备美国 VC 融资和股票期权安排的项目，可优先评估 Delaware C-Corp。这是基于经营和维护成本的判断，不是银行批准保证。

## 公司类型和注册州

| 情况 | 优先评估的方案 | 原因 |
|---|---|---|
| 一人经营软件、咨询、跨境服务，无机构融资计划 | 单成员 LLC | 组织相对简单，但外资持有仍有税务申报 |
| 多人合伙 | 多成员 LLC，或按融资计划选择 C-Corp | 明确股权、分配、退出；税务通常更复杂 |
| 美国VC融资、股票和期权安排 | Delaware C-Corp | 股权安排标准化，持续法律和税务成本更高 |
| 已有美国办公室、员工等实际活动 | 先评估实际经营州 | 其他州成立后，仍可能在经营州登记并承担两地义务 |

LLC 是法律组织形式，不等于免税公司。默认单成员 LLC 通常按 disregarded entity 处理，多成员通常按 partnership 处理，也可依法选择其他分类。美国税务上的非居民外国人不能成为 S-Corp 股东。[IRS LLC 分类](https://www.irs.gov/businesses/small-businesses-self-employed/limited-liability-company-llc)、[S-Corp限制](https://www.irs.gov/businesses/small-businesses-self-employed/s-corporations)

| 方案 | 成立政府费 | 州年度维护费用 | 时间 |
|---|---:|---:|---|
| Wyoming LLC | $100，自行在线当前合计$102.40 | $60起，或州内使用资产×0.0002，取较高者；在线支付费另计 | 成立周年月份第1日到期 |
| Delaware LLC | $110 | 2026税年起$400/年，无LLC年报 | 次年6月1日前 |
| Delaware C-Corp | $109起，受股份设置、页数影响 | 年报$50，加franchise tax；两算法最低税分别$175、$400 | 通常次年3月1日前 |

来源：[Wyoming成立](https://wyobiz.wyo.gov/Business/RegistrationInstr.aspx)、[州年报](https://wyobiz.wyo.gov/Business/AnnualReport.aspx)、[资产口径](https://sos.wyo.gov/FAQS.aspx?root=BUS)、[Delaware费表](https://corpfiles.delaware.gov/Fee_Schedule/AugustFee2026.pdf)、[LLC年税](https://corp.delaware.gov/alt-entitytaxinstructions/)、[2026年生效修法](https://legis.delaware.gov/json/BillDetail/GenerateHtmlDocumentSessionLaw?docTypeId=13&sessionLawId=143069&sessionLawName=chp273)、[C-Corp年税](https://corp.delaware.gov/frtaxcalc/)。

Delaware LLC“每年$300”已是旧数字；2026年成立的LLC应为2027年6月1日前缴款预留$400，年税不按月份折算。C-Corp税额需按股本与资产计算，不能一律只预算最低额。

Wyoming注册不自动免除其他州义务。达到加州 doing-business 条件的 LLC 通常仍涉及加州$800年税，但不能仅因有加州客户就机械认定必须缴纳。[加州FTB规则](https://www.ftb.ca.gov/file/business/types/limited-liability-company/index.html)

## 注册公司

1. 确定名称及备选、唯一或多位成员的真实身份和持股、真实业务、经营与收信地址。
2. 选择州内合格注册代理；代理接收法律文书，须持续维护，不等于美国办公室或合格银行地址。
3. 自行通过州政府提交，或委托代办提交；不要重复申请。核对政府费、服务费、代理续费、加急、EIN和订阅。
4. 保存州备案成立文件、编号、收据，核对全部拼写。
5. LLC保存 Operating Agreement；Corporation保存 bylaws、董事和股权文件。内部协议不等于额外一次州注册。[Delaware官方FAQ](https://corp.delaware.gov/faqs/)

Wyoming 符合条件的在线流程完成后即可 active；纸件不超过15个工作日。Delaware普通件随队列变化；Atlas产品文档预计成立1–2工作日，包含其加急安排。成立不代表EIN和银行同步办好。[Wyoming指南](https://sos.wyo.gov/Business/Docs/HowToCreateAWyomingCompany.pdf)、[Atlas时间](https://docs.stripe.com/atlas/signup)

## 申请 EIN

IRS申请免费。先成立公司，再申请EIN；代办费用是服务费，没有常规“每年续EIN”费用。IRS在线申请有美国主要经营地点及负责人SSN/ITIN等要求，无号码的大陆申请人不能照搬即时在线教程。[IRS入口](https://www.irs.gov/businesses/small-businesses-self-employed/get-an-employer-identification-number)

1. 下载当前 [SS-4正式表格](https://www.irs.gov/pub/irs-pdf/fss4.pdf)，按[逐行说明](https://www.irs.gov/instructions/iss4)填写。
2. 公司名称按成立文件，收信和实际地址分别写；7a填写真实负责人，不能用代办替代实际负责人。
3. 无号码且不具备取得SSN/ITIN资格时，7b依说明填 `foreign` 或 `N/A`。没有号码不自动等于没有资格，也不意味着必须先买ITIN。
4. 按成员数量、税务分类、雇员等真实事实填写并签署。
5. 本路线采用传真或邮寄，按实际主要经营地、办公室及传真发送地选正确路由，保留成功凭证，不重复申请。
6. 保存回传EIN及CP575，必要时索取147C；不要把普通号码截图当成银行当然接受的证明。

IRS更具体操作手册将美国成立LLC归为Domestic，不能据概述页面承诺国际电话即时发号。本路线中国主要经营、无美国主要办公室，从境外发送当前传真为+1 304-707-9471；从美国发送为855-215-1627。传真服务实际发送地须确认，提交前重核当日说明。完整逐行示例见《Wyoming操作清单》。[IRS操作手册](https://www.irs.gov/irm/part21/irm_21-007-013r)

当前IRS动态进度：传真收到后约8工作日处理、纸件收到后30天内；另留补件及证明送达时间，不把常规约4天说明当成当前保证。[处理进度](https://www.irs.gov/help/processing-status-for-tax-forms)

## 申请 Mercury 企业户

准备成立文件、EIN证明、持股≥25%的受益所有人及至少一名管理负责人的身份信息，国际申请人使用有效护照；另备真实地址证明、业务、资金来源和美国联系材料。

Mercury FAQ允许EIN待批时用完整SS-4申请，获批90天内补正式EIN；帮助中心仍列IRS-issued证明。本指南先拿正式证明再申请，同时保留例外，不承诺受理和批准。[FAQ](https://mercury.com/faq)、[材料清单](https://support.mercury.com/hc/en-us/articles/28770957425172-Gathering-your-documents)

| 地址字段 | 要点 |
|---|---|
| 法定地址 | 符合Mercury美国实体地址要求，不是PO Box或虚拟办公室 |
| 实际经营地址 | 可以是中国真实住宅；不得以注册代理、虚拟邮箱或收信中心替代 |
| 股东居住地址 | 真实住址；按要求提供可核验材料 |
| 收件地址 | 寄卡按投递要求；收件资格不等于经营/居住证明 |

从 [Mercury官方企业入口](https://mercury.com/business-banking)填写公司、EIN、业务、资金来源、地址及股权，完成上传和身份验证。提交确认In Review，及时查邮件及垃圾邮件补件。官方通常0–2工作日决定，补件可能延长。基础账户无开户费、必需月费或最低余额要求，部分高级功能、外币或特殊交易另收费。[地址规则](https://support.mercury.com/hc/en-us/articles/28769699533588-Company-address-requirements)、[审核流程](https://support.mercury.com/hc/en-us/articles/28771494745364-What-happens-after-I-submit-my-Mercury-business-account-application)

美国业务联系可能继续核验，订单、合同、发票应真实且与收付款相符。尚未开展业务就具体写计划，不编造流水、美国员工和办公室。[持续核验](https://support.mercury.com/hc/en-us/articles/53171397356820-Verifying-your-U-S-business-operations)

## 费用和总体时间

以下是公开报价样例，用于预算拆解，不构成服务推荐或开户承诺。

| 环节 | 费用样例 | 时间 |
|---|---:|---|
| Wyoming政府注册 | $100；自行在线合计$102.40 | 在线完成或纸件审核 |
| Northwest注册代办 | $39＋州费，含首年代理；续费$125/年 | 随州和服务变化 |
| 自行EIN | IRS $0；传真/邮寄另计 | 当前传真约收件后8工作日处理 |
| Northwest无SSN EIN服务 | $200 | 不据付费推定必然加速 |
| Stripe Atlas | $500，含Delaware州费、EIN、首年代理；续费$100/年 | 成立约1–2工作日；无SSN EIN预计成立后10–35工作日 |
| Mercury基础企业户 | 开户$0，无必需月费 | 通常0–2工作日决定，补件另计 |
| 标准外资单成员LLC税表服务 | Hiltzik公开报价$599/税务周期 | 标准范围需书面确认，税款和额外项目另计 |

来源：[Northwest成立](https://www.northwestregisteredagent.com/incorporation-service)、[EIN服务](https://www.northwestregisteredagent.com/start-a-business/ein-tax-id)、[Atlas价格](https://stripe.com/atlas)、[Atlas时间](https://docs.stripe.com/atlas/signup)、[Hiltzik税务报价及范围](https://hiltzikcpa.com/form-5472-filing-service/)。

按最终Wyoming路线，连续两个12个月的基础预算：自行EIN首年$799.44，购买EIN服务首年$999.44，次年均$785.44。包含一份州年报及一周期$599标准税表服务；两年基础分别$1,584.88或$1,784.88。结账附加费、传真、合格地址、网站、额外记账/税表、实际税款、交易与注销费用另按实际计，未知项目不能默认为零。完整逐项表见《Wyoming操作清单》和预算JSON。

无SSN的全流程建议预留约4–8周，这是排期余量而非官方承诺；可能更快，也可能因补件更久。宣传“两天开始收款”不等于Mercury两天必获批。

## 成立以后不能遗漏的义务

- Wyoming LLC：周年月份第1日处理年报及license tax；最低额在线支付当前合计$61.44。
- Delaware LLC：通常次年6月1日前缴年税；C-Corp通常次年3月1日前处理年报及franchise tax。
- 外国人全资持有的美国disregarded entity有应申报关联交易时，通常须报Form5472＋pro forma1120。成立相关费用、股东出资和分配都可能触发，零收入或未开户不自动免申报。漏报基础罚款$25,000。[IRS5472](https://www.irs.gov/instructions/i5472)
- 日历年度适用联邦申报通常次年4月15日前，需延期应在原截止日前处理；不是成立满一年才考虑。[1120截止](https://www.irs.gov/instructions/i1120)、[7004延期](https://www.irs.gov/instructions/i7004)
- 美国境内成立公司目前获FinCEN BOI豁免，不免除IRS税表或银行受益所有人资料要求。[FinCEN当前规则](https://www.fincen.gov/boi)
- 多成员、主动选择公司税制、美国雇员、库存、多州经营和不同收入会改变义务。美国处理不自动免除中国税务居民的中国义务，注册前确定负责人、税表范围和回执。

## 付款与维护避坑

1. 不接受“开户包过”“美国IP必过”“Atlas必过”等承诺。
2. 逐项核对赠送地址、邮件扫描、税务信件、年报、代理、电话和网站的续费及取消条件。
3. EIN免费且无常规年续费；代办收服务费，不等于IRS收费。
4. 海牙认证、印章未被列为Mercury基础申请统一必备项，不默认加购。
5. 不虚构美国住址、业务、合同、行业或资金来源，不擅自改动原始账单。
6. 获批后保留股东出资、代付、借款、分配及业务流水。初始入金是公司资产，不是开户手续费。
7. 不经营时正式处理注销、结税和订阅，不能只停止登录银行。
'''


def write_text(name, text):
    (REPO / 'content' / name).write_text(text, encoding='utf-8')


def dated(text):
    first, rest = text.split('\n', 1)
    return first + '\n\n' + META + rest.lstrip('\n')


def export():
    for name in ['content', 'data']:
        (REPO / name).mkdir(parents=True, exist_ok=True)
    catalogue = json.loads((RESEARCH / 'catalogue.json').read_text())
    public_fields = [
        'id', 'title', 'url', 'canonical_url', 'alias_urls', 'platform', 'domain',
        'author', 'published_at', 'date_basis', 'content_type', 'language',
        'accessed_at', 'read_status', 'findings', 'commercial',
        'registration_outcome', 'limitations', 'content_cluster_key',
        'dedupe_reason', 'curator_status', 'date_conflict', 'curator_note',
        'curator_claim', 'curator_observation', 'evidence_grade',
        'reviewed_source_url', 'review_limitations', 'review_date_basis',
        'decision_support',
    ]
    public = [{key: row.get(key) for key in public_fields} for row in catalogue]
    encoded = json.dumps(public, ensure_ascii=False, indent=2) + '\n'
    assert len(public) == 142
    assert not re.search(r'/Users/|file://|localhost|127\.0\.0\.1', encoded)
    assert len({x['id'] for x in public}) == 142
    (REPO / 'data' / 'catalogue.json').write_text(encoded)

    summary = json.loads((RESEARCH / 'run_summary.json').read_text())
    keep = [
        'schema', 'topic', 'as_of', 'scope', 'agents_executed', 'query_count',
        'raw_observations', 'total_candidates', 'duplicate_observations_collapsed',
        'original_url_count', 'distinct_source_domains', 'by_platform',
        'by_curator_status', 'by_language', 'by_commercial', 'publication_years',
        'official_reference_count', 'accepted_body_count', 'accepted_metadata_count',
        'weak_body_verified_count', 'weak_metadata_verified_count',
        'decision_grade_body_count', 'by_evidence_grade',
    ]
    summary = {k: summary[k] for k in keep}
    summary['published_at'] = '2026-10-24'
    summary['limitations'] = [
        '142条为本次公开检索形成的内容记录，不是全网帖子总量。',
        '110条原文独立核验、4条仅元数据核验、17条访问受阻、11条排除，分别展示。',
        '原文核验只说明原页支持所记窄主张；申请成功或失败仍是作者/评论者自述，未独立核实银行账户或全部材料。',
        '同一讨论可能包含多位用户的相反经历；结果标签不是独立申请样本，不计算成功率。',
        '22条已核原文和4条元数据仍属weak；88条原文证据为strong/medium。',
        '63条明确商业/联盟/代办内容；32条商业属性unknown，不将其视为非商业。',
        '78条发布日期未知；不将相对时间或页面更新时间擅自当成发布日期。',
        '转载、语言镜像和同一作者经历链不构成新增成功申请人。',
        '未系统采集可比互动指标，不作热度排名。登录、robots、验证码和限流造成覆盖缺口。',
        '此次发布为2026-10-23核验资料的公开整理版，发布日不是再次核验日期。',
    ]
    summary['platform_labels'] = {
        'bilibili':'B站', 'github':'GitHub', 'hacker_news':'Hacker News',
        'independent_web':'独立网站/博客', 'linkedin':'LinkedIn', 'linuxdo':'Linux.do',
        'medium':'Medium', 'mercury_official':'Mercury官方', 'reddit':'Reddit',
        'v2ex':'V2EX', 'x':'X/Twitter', 'youtube':'YouTube',
    }
    summary['status_labels'] = {'verified':'原文独立核验','metadata_verified':'仅元数据核验','blocked':'访问受阻','excluded':'排除'}
    (REPO / 'data' / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')

    budget = json.loads((CHECKLIST / 'budget.json').read_text())
    (REPO / 'data' / 'budget.json').write_text(json.dumps(budget, ensure_ascii=False, indent=2) + '\n')

    original = (RESEARCH / 'report.md').read_text()
    intro = original.split('## 内容清单')[0]
    intro = intro.replace('实际完成情况以agent_registry.json及各分片产物为准。', '原始研究按此分工完成；本公开版不发布内部执行日志或私人申请材料。')
    intro = intro.replace('[打开可筛选总表](dashboard.html) · [下载文字总表](帖子总表.tsv) · [查看全部JSON](catalogue.json)', '[下载142条公开目录JSON](../data/catalogue.json) · [查看统计和局限JSON](../data/summary.json)')
    intro = intro.replace('备齐成立文件、IRS出具EIN文件、国际申请者护照；未处理的SS-4申请表不能当作IRS返回文件。', '备齐成立文件、IRS出具EIN文件、国际申请者护照。补充修正：Mercury主站FAQ允许EIN待批时凭完整SS-4申请，并在获批后90天内补正式EIN；自行填写SS-4不等于IRS返回证明。本文操作主线先拿正式EIN再申请。[官方FAQ](https://mercury.com/faq)')
    intro = intro.replace('28渠道的路线状态见platform_coverage.tsv；本次不作‘20+平台完成’声明。', '发现渠道不等于完成原文采集的平台；本次不作“20+平台完成”声明。')
    intro = intro.replace('没有系统采集可比互动指标，因此不声称“最热”或“Top50”。', '没有系统采集可比互动指标，因此不作热度排名。')
    labels = summary['platform_labels']
    status = summary['status_labels']
    rank = {'verified':0,'metadata_verified':1,'blocked':2,'excluded':3}
    def escape(value):
        return str(value).replace('|','\\|').replace('\n',' ')
    rows = []
    for x in sorted(public, key=lambda x: (rank[x['curator_status']],x['platform'],x['id'])):
        commercial = '是' if x['commercial'] is True else '否' if x['commercial'] is False else '未知'
        rows.append('| ' + ' | '.join([
            x['id'], f"[{escape(x['title'])}]({x['url']})", labels.get(x['platform'],x['platform']),
            x['published_at'] or '未知', status[x['curator_status']],x['evidence_grade'],commercial,
        ]) + ' |')
    table = '\n## 142条内容清单\n\n按核验状态、平台和稳定ID排列，不表示热度或质量排名。排除项保留以便了解边界，不用于支持开户结论。详细窄主张、结果标签、日期依据、商业属性及限制见公开目录JSON。\n\n| 编号 | 内容 | 来源 | 发布日期 | 复核状态 | 证据等级 | 商业属性 |\n|---|---|---|---|---|---|---|\n' + '\n'.join(rows) + '\n'
    tail = '''
## 去重、反例和缺口

- URL追踪参数、V2EX区域镜像、Reddit帖子ID、视频ID归一；明确的同文语言版本保留别名，不重复计内容。
- V2EX1140290与Meepo博客保留两个帖子记录，但共享同一作者经历链；二手汇总不能新增成功申请人数。
- 同一讨论可能同时有被拒主帖和获批评论，不能把文章数当申请数。
- 登录限制、robots、验证码、限流和部分原页不可达造成缺口，受阻项如实保留。
- 平台未召回内容不证明平台没有相关帖子。未核验和排除项不得作为当前政策依据。

## 本次发布口径

本版整合公开研究、核心结论、公司/EIN/开户完整流程及最终Wyoming操作清单。只发布公共来源字段、原创整理和模板；不发布私人证件、申请资料、凭证、执行日志或完整第三方文章。资料核验截至2026-10-23，2026-10-24为发布日。费用与政策应在实际提交前复核。

Mercury企业户与Personal条件分开。税务、费用和提交示例以《Wyoming操作清单》的最终修正为准；pending EIN例外、IRS传真/邮寄路线及Hiltzik $599预算已同步。
'''
    write_text('research.md', dated(intro + table + tail))
    write_text('conclusions.md', dated(CONCLUSIONS))
    write_text('full-process.md', dated(FULL_PROCESS))
    checklist = (CHECKLIST / '操作清单.md').read_text()
    checklist = checklist.replace('核验日期：2026-10-23。金额均为美元。', META.strip())
    checklist = checklist.replace('加州费', '＋州政府费')
    write_text('checklist.md', checklist)
    write_text('business-template.txt', (CHECKLIST / 'Mercury业务说明模板.txt').read_text())

    catalogue_md = ['# 142条公开内容目录', '', META.strip(), '',
        '本目录收录142条内容记录，包括110条原文核验、4条仅元数据核验、17条访问受阻、11条排除。核验只说明原页支持所记录窄主张，不等于独立证实银行申请结果；approved/denied/mixed是来源自述或讨论内容标签，不是总体申请样本。商业未知不等于非商业；未知日期保持未知。不复制原帖全文或批量摘录。', '']
    for number, x in enumerate(sorted(public, key=lambda x: (rank[x['curator_status']],x['platform'],x['id'])), 1):
        commercial = '明确商业/联盟/代办' if x['commercial'] is True else '未见明确商业属性（本次核验）' if x['commercial'] is False else '未知'
        claim = x['curator_claim'] or x['findings'] or '仅作发现线索，未形成可支持开户结论的窄主张。'
        limitations = x['review_limitations'] or x['limitations'] or '没有足够信息独立核实具体申请材料及银行结果。'
        catalogue_md.extend([
            f"## {number}. {x['title']}", '', f"POST-ID: {x['id']}", '',
            f"[打开原始来源]({x['url']})", '',
            f"来源：{labels.get(x['platform'],x['platform'])}；作者：{x['author'] or '未知'}；发布日期：{x['published_at'] or '未知'}；访问/核验日：{x['accessed_at'] or '2026-10-23'}。", '',
            f"复核：{status[x['curator_status']]}；证据等级：{x['evidence_grade']}；商业属性：{commercial}；来源内容/自述结果标签：{x['registration_outcome']}。", '',
            f"整理的窄主张：{claim}", '', f"限制：{limitations}", '',
            f"日期依据：{x['review_date_basis'] or x['date_basis'] or '未找到可核验的绝对发布日期；保持未知。'}", '',
        ])
    write_text('catalogue.md', '\n'.join(catalogue_md))

    index = [
        {'id':'research','title':'142条公开内容研究','file':'research.md','description':'原文核验、来源分布、商业标记与统计局限'},
        {'id':'conclusions','title':'企业户与个人户结论','file':'conclusions.md','description':'大陆用户资格、材料、地址、拒绝风险及自述案例'},
        {'id':'full-process','title':'美国公司到Mercury完整流程','file':'full-process.md','description':'公司类型与州选择、EIN、开户、费用、排期及持续义务'},
        {'id':'checklist','title':'Wyoming单成员LLC操作清单','file':'checklist.md','description':'无SSN/ITIN路线、SS-4逐行示例、业务模板及两年预算'},
    ]
    write_text('index.json', json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    assert sum(collections.Counter(x['curator_status'] for x in public).values()) == 142
    assert sum(x['published_at'] is None for x in public) == 78
    assert sum(x['commercial'] is True for x in public) == 63
    for name in ['research.md','conclusions.md','full-process.md','checklist.md','business-template.txt','catalogue.md']:
        text = (REPO/'content'/name).read_text()
        assert not re.search(r'/Users/|file://|localhost|127\.0\.0\.1',text), name
    assert len(re.findall(r'^POST-ID: M', (REPO/'content'/'catalogue.md').read_text(),re.M)) == 142
    print(json.dumps({'documents':len(index),'catalogue_records':len(public),'status_counts':dict(collections.Counter(x['curator_status'] for x in public)),'unknown_dates':78,'commercial_records':63,'budget_first_self':budget['first_period_self_ein']['subtotal'],'budget_first_assisted':budget['first_period_assisted_ein']['subtotal'],'budget_second':budget['second_period']['subtotal']},ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research-package', required=True, type=Path)
    parser.add_argument('--checklist-package', required=True, type=Path)
    args = parser.parse_args()
    RESEARCH = args.research_package.resolve()
    CHECKLIST = args.checklist_package.resolve()
    export()
