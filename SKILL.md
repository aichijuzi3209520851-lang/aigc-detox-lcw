---
name: aigc-detox-lcw
description: 中文学术/技术写作降 AI 味一体化工作台：机械信号体检 → 三层诊断 → 带事实护栏的改写 → 改写后复检闭环。支持 DOCX 与纯文本、中英双语，产出 HTML/PDF 报告与 Word 修订痕迹，改写前后自动比对，确保风险真降且引用数字不丢。Use when the user asks to 降低AI率、去AI味、降AIGC、AIGC检测、AI痕迹消除、论文降重、人工润色、humanize、学术文本人工化，or wants a paper's AI-writing-rate report.
---

# aigc-detox-lcw：降 AI 味一体化工作台

五个前身（chinese-thesis-workbench / humanizer-zh-academic / aigc-down-skill / ai-check / aigc-detector）
经 6 道带真值的对抗测试后合并而成。**每一段的取舍都有实测依据，见 `references/benchmark.md`。**

---

## 0. 三条不可越过的前提

| # | 前提 | 违反后果 |
|---|---|---|
| 1 | **这不是检测器**。产出的是"确定性文本信号 + 诊断意见"，**不是**任何平台的 AIGC 百分点 | 不许说"AI 率 87%""已降到 5%"，不许声称对齐知网/维普/Turnitin |
| 2 | **事实是只读的**。数字、引用标记、模型名、指标、结论方向一律不得改动 | 改坏了就是学术事故，脚本会拦，但不要指望脚本兜住所有 |
| 3 | **不动原文件**。所有改写写入新文件 | `aigc_detox_lcw_rewrite.py` 拒绝 out 与源同名 |

---

## 1. 工作流（七步，缺一步都不算完成）

```
①  判定输入形态      → ② 机械体检 → ③ 三层诊断 → ④ 出报告并停下等确认
                                              ↓
⑦  交付（复检 PASS）← ⑥ 复检闭环 ← ⑤ 生成替换 → dry-run → 带护栏 apply
```

**第 ①–④ 步永远先做。** 除非用户明说"直接改"或正文 ≤ 300 字，否则**出完报告就停**，等用户点头。

---

### ① 判定输入形态

| 输入 | 走法 |
|---|---|
| `.docx` | 全套。`aigc_detox_lcw_scan.py scan` → 后续所有脚本都用它 |
| 纯文本 / 粘贴 | 跳过 ②，直接用 §3 的人工诊断清单；如要复检，先把改前改后各存成一个 `.docx` |
| `.pdf` | 先转 `.docx`，不要直接改 PDF |
| 英文正文 | 支持。语言判定：前 500 字符中文占比 > 60% 即 zh，否则 en |

同时确认**文体档位**（决定改写力度，见 §4）。

---

### ② 机械体检（`aigc_detox_lcw_scan.py`）

```bash
python scripts/aigc_detox_lcw_scan.py scan "<论文.docx>" --out scan.json
python scripts/aigc_detox_lcw_scan.py features "<论文.docx>"          # 只看信号，出 chunk 之前先摸底
```

产出每个 chunk 的 `traceFeatures`：

- **风险信号**：模板短语 / 句式节奏过于均匀 / 小句节奏过于均匀 / 连接词密集 / 破折号偏多 / 泛化套话 / 贡献罗列结构 / 目标表述泛化
- **缓解信号**：具体证据 / 领域方法细节 / 定量结果支撑 / 限制条件说明

> **缓解信号是这套工具最值钱的部分。** 前身 ctw 只有风险项、没有缓解项，
> 结果把一篇有 92.7%/n=1200/[12] 的硬核论文也判成有风险（实测误差 7 vs 本工具 1）。
> **看到缓解信号多的段落，默认它是人写的，不要去改它。** 改了才是破坏。

---

### ③ 三层诊断（这是本 skill 与前身最大的差别）

单看"有没有模板词"会把隐身 AI 全部放过去。必须三层都看：

**第一层 · 词面** —— 脚本给，客观。
模板短语、泛化套话、AI 高频词、连接词密度、破折号密度。
**这一层查不出东西，不代表没问题。**

**第二层 · 节奏** —— 脚本给，客观。**抓隐身 AI 的唯一有效手段。**
看 `sentenceLengthCV`（句长变异系数）：

| CV | 判断 | 处理 |
|---|---|---|
| < 0.30 且句数 ≥ 4 | 节奏过于均匀 | **重点**：这是模板词全无、但一眼像 AI 的文本 |
| 0.30 – 0.45 | 正常 | 不动节奏 |
| > 0.45 | 长短交错，是人味 | **不要为了"整齐"去改** |

**句数只有 2–3 句的长段落（≥150 字）是句级检查的盲区**，脚本会自动切到小句级
（按 `，、；。：` 切）再量一次，命中则报**另一个标签**「小句节奏过于均匀」，
阈值 `clause_cv < 0.45`。这是 2026-11 用 PaperPass 标红版当标签语料反推出来的：
标红段落召回从 18.2% 提到 31.8%，六道基准题一个都没变。**它只在句级沉默时发言，
永远不会压制已有信号**——所以看到这个标签不代表比「句式节奏过于均匀」更严重。

> 实测：一份零模板词、8 句全部 24–30 字的隐身 AI，CV = **0.064**。
> 五个前身里只有 ai-check 抓住了它；humanizer / aigc-down / ctw 全部漏判，
> 因为它们的判据全建立在"模板词是否出现"上，无词可抓即放过。

**第三层 · 语义** —— 模型给，**主观，必须标出来**。

用下面五个维度**做描述，不给分数**：

| 维度 | 问什么 |
|---|---|
| 句式规整度 | 句子骨架是否高度同构（同一"主体+状语+谓语+长宾语"反复） |
| 逻辑词密度 | 是否靠"首先/其次/因此/综上"推进而非靠内容推进 |
| 语态特征 | 主语是不是清一色"平台/系统/研究者"这类泛指角色 |
| 词汇多样性 | 抽象双名词并列（"层级化呈现与路径化组织"）是否过密 |
| 论证深度 | 有没有边界、失败案例、作者取舍、可检验推论 |

> **为什么这一层不许给分数**：前身 aigc-detector 用五维加权打 0–100 分，
> 六道测试全对，但它自陈"没有检测引擎，分数是模型读完主观给的"。
> 换个模型、换个温度，分数就变。**看起来最准的那个，恰恰是最不可复现的。**
> 所以这里只保留它的维度名称当诊断清单，扔掉它的数字。

---

### ④ 出报告并停下

报告必须包含：

1. 文档概况（标题、总字数、chunk 数）
2. **逐 chunk 三列表**：风险信号 / 缓解信号 / 三层诊断结论
3. **需要改的段落**，按优先级排序（先改风险信号 ≥ 2 的）
4. **明确写出不该改的段落**及理由（缓解信号多的、CV > 0.45 的）
5. 一句诚实的边界声明

报告首行固定写：

```
本报告给出的是文本特征与改写建议，不是任何平台 AIGC 检测的预测值。
```

然后**停**。等用户确认改哪些。

---

### ⑤ 生成替换 → dry-run → 带护栏 apply（`aigc_detox_lcw_rewrite.py`）

**绝不改原文件。** 流程固定三步：

```bash
# 1. 先跑 dry-run，看每一处能不能落地
python scripts/aigc_detox_lcw_rewrite.py dry-run "<原.docx>" replacements.json

# 2. 有 willApply=false 的，改 JSON 再来一遍，直到全绿

# 3. 写入新文件（可选 Word 修订痕迹）
python scripts/aigc_detox_lcw_rewrite.py apply "<原.docx>" replacements.json \
       --out "<原-去AI味.docx>" --track-changes
```

`replacements.json` 格式：

```json
{"replacements": [
  {"chunkId": "c1",
   "sourceText": "与原文逐字一致的整段",
   "replacementText": "改写后的整段",
   "occurrence": 1,
   "allowNumberChange": false}
]}
```

**脚本会拦下的情况**（实测有效，不是声明）：

| 拦截原因 | 说明 |
|---|---|
| `missing citation marks: [12]` | 改写后少了引用标记 → 拒绝 |
| `missing numbers: 92.7, 3.2` | 改写后少了数字 → 拒绝 |
| `sourceText not found` | 原文对不上（多半是复制时改了标点）→ 拒绝 |
| `sourceText matched multiple paragraphs` | 同一段出现多次 → 要求给 `occurrence` |
| `occurrence out of range` | 序号超了 → 拒绝 |

> `allowNumberChange` 只在用户**明确同意**改数字时才可置 true。默认 false。
> 实测：把"92.7% 的准确率[12]"改写成"很高的准确率"，dry-run 直接判 `willApply: false`，
> 同时列出缺 `[12]`、缺 `92.7`、缺 `3.2`。**护栏是真的。**

---

### ⑥ 复检闭环（`aigc_detox_lcw_compare.py`）—— 五个前身全都没有的一步

```bash
python scripts/aigc_detox_lcw_compare.py "<原.docx>" "<原-去AI味.docx>"
python scripts/aigc_detox_lcw_compare.py a.docx b.docx --json diff.json
```

它回答三个问题：

1. **风险真的降了吗** —— 风险信号数、模板短语数、泛化套话数、连接词密度的前后差值
2. **事实坏了吗** —— 丢失的引用、丢失的数字、新增的数字
3. **改出了新毛病吗** —— 新引入的风险信号、**句长是否被改得更均匀**

判定：

| 结论 | 条件 | 动作 |
|---|---|---|
| **FAIL** | 丢引用 / 丢数字 | 必须回 ⑤ 重做 |
| **WARN** | 风险未降、或新增风险、或节奏被压平 | 逐条看，可接受则记录理由后交付 |
| **PASS** | 风险下降且无上述问题 | 交付 |

> **这一步抓到过一个真实问题**：一次看起来很好的改写，把 CV 从 0.534 压到 0.272，
> 掉进"句式节奏过于均匀"区间——**去掉了模板词，却顺手把文本改成了另一种机器味**。
> 五个前身没有任何一个会告诉用户这件事，它们改完就收工。
>
> **注意**：源文本 CV 本来就 < 0.3 时，改写后仍低是正常的（不是回归）。
> 脚本区分 `regression`（源正常、改后均匀）与 `flattened`（被压平）。

---

### ⑦ 交付

交付物：

- `<标题>-去AI味.docx`（新文件，可带修订痕迹）
- `<标题>-AI特征报告.html`（可选 PDF）
- `<标题>-复检报告.json`（`aigc_detox_lcw_compare.py --json` 的产出）
- 一页变更说明：改了哪些段、为什么、哪些**故意没改**、复检结论

---

## 2. 强制硬约束（输出前逐项核对，命中即修复）

| 约束 | 上限 | 说明 |
|---|---|---|
| AI 高频词（见 §5 词表） | 每段 ≤ 2 个 | 超出必须替换 |
| 段末总结套句（"此案例XX了""由此可见"） | 全文 ≤ 1 处 | 超出删或改 |
| 整齐三元并列 | 每段 ≤ 1 处 | 超出必须打破对称 |
| "依据/基于XX理论"开头 | ≤ 20% 段落数 | 超出移位到段中 |
| 正文加粗 | 全文 ≤ 5 处 | 超出削减 |
| 泛化结尾（"具有重要意义"类） | 全文 0 处 | 命中即改 |
| 模糊归因（"专家认为"无出处） | 全文 0 处 | 命中即删或具体化 |
| **引用与数字** | **零丢失** | 硬红线，脚本会拦 |
| **改写后 CV** | 不得低于源文本 60% | 防"改得更整齐" |

---

## 3. 人工诊断清单（纯文本输入、或给脚本结果做补充时用）

每命中一项 +1 分，**≥ 4 分 = 高风险段落**。

**词面（第一层）**
- [ ] 段首含「依据/基于 XX 理论」
- [ ] 段末含「此案例 XX 了」或「由此可见」
- [ ] 含整齐的「首先/其次/再次」三段论
- [ ] 含「该处理/该设计……体现了……」
- [ ] 含「XX 面临的核心问题是」
- [ ] 含模糊归因（「专家认为」无出处）
- [ ] 含填充短语（「值得注意的是」「不难发现」）
- [ ] 结尾为泛化结论

**结构（第二层）**
- [ ] 三个以上完全对称的并列句
- [ ] **句长全部落在同一区间（无长短交错）← 单独命中就值得警惕**
- [ ] 相邻多段结构高度雷同
- [ ] 全文无一处具体数字、案例、引文

**语义（第三层）**
- [ ] 主语全是泛指角色（平台/系统/研究者/管理者）
- [ ] 抽象双名词并列过密
- [ ] 零边界、零失败案例、零作者取舍

> **反向清单（命中这些说明是人写的，不要改）**
> 有可核的具体数字 / 有明确的归因与出处 / 承认局限与不确定性 / 有"我们起初以为……但数据不支持"这类转折 / 有失败案例与占比 / 局部的口语或迟疑。

---

## 4. 文体标定（改写前必须确认档位）

| 类型 | 第一人称 | 口语化容忍 | 破折号 |
|---|---|---|---|
| 期刊论文 | 少用，"本文"优先 | 低 | 适中偏少 |
| 毕业论文 | 可用"笔者" | 中 | 适中 |
| 研究报告 | "本报告/本研究" | 中低 | 少 |
| 学术博客 / 评论 | 自由用"我" | 中高 | 适中 |
| 技术文档 / 工程报告 | 少用 | 低 | 少 |

> 前身 aigc-down-skill 只有"毕业论文"一档，合并时补全为五档。

---

## 5. 改写手法（按优先级执行）

**顺序很重要：先动结构，再动词。只换词不改句式，等于没改。**

1. **移位** —— 理论名从段首移到段中，让它成为论证的一部分而非开场白
2. **砍尾** —— 删掉段末的总结套句。话已经说完了，不要再总结一遍
3. **破对称** —— 三元并列拆成两项，或让三个分句长短不一
4. **错节奏** —— **把长句拆一个短的出来，或把两个短句并成长句。这是治隐身 AI 的关键一步**，前 3 步治不了它
5. **换词** —— AI 高频词替换，优先处理前四项（见下表）
6. **去模糊** —— 删填充短语；模糊归因要么补出处，要么删
7. **注视角** —— 加入研究者的判断、意外、取舍、疑惑

**AI 高频词替换表（优先处理前 4 项）**

| 原词 | 替换方向 |
|---|---|
| 深刻揭示了 | 说明了 / 指出了 |
| 具有重要意义 | 直接说结论，或删掉整句 |
| 综合运用 | 结合 / 用 |
| 不可或缺 | 离不开 |
| 深入探讨 / 系统梳理 / 理论支撑 / 有效解决 / 充分说明 | 按上下文换成具体动作 |
| 进一步 / 至关重要 / 赋能 / 助力 / 抓手 / 闭环 | 删或具体化 |

**英文侧高频腔调词**：pivotal / delve / underscore / leverage / seamless / multifaceted /
intricate interplay / paving the way / cutting-edge / holistic / paramount / realm /
sheds light on / promising avenues / It is important to note / In conclusion。

---

## 6. 噪声保留（别改过头）

**不要把所有段落改得风格一致。** 全消干净会因过度均质化触发另一类检测。

每千字允许保留 **2–3 处**轻微 AI 特征：

- 首选保留：轻微的两项并列（非三元对称）
- 次选保留：「值得注意的是」这类轻过渡词（全文 ≤ 1 处）
- **绝不保留**：「此案例印证了」「具有重要意义」——权重太高

---

## 7. 常见误区（前身踩过的坑）

| 误区 | 为什么错 |
|---|---|
| 只换词不改句式 | 检测看的是结构，词换了结构还在，等于没改 |
| 只改首尾两段 | 中间才是主体，改首尾只是做了个样子 |
| 往文章里插错别字 | 学术稿插错别字是自毁，且不降低结构相似度 |
| 全文改成口语 | 论文语域崩了，比 AI 味更致命 |
| 用模糊归因替换具体引用 | 把唯一可信的证据换成更不可信的 |
| **改得比原文更整齐** | 复检会报 WARN。整齐本身就是机器味 |
| 把所有痕迹清干净 | 过度清洁反而异常，见 §6 |
| 声称"已通过检测" | 本工具不做这种承诺，见 §0 |

---

## 8. 脚本速查

| 脚本 | 作用 | 依赖 |
|---|---|---|
| `scripts/aigc_detox_lcw_scan.py` | DOCX → chunk + 机械信号（scan / report / features） | python-docx, reportlab |
| `scripts/aigc_detox_lcw_rewrite.py` | 带引用/数字护栏的 DOCX 改写（dry-run / apply，可带修订痕迹） | python-docx |
| `scripts/aigc_detox_lcw_compare.py` | 改前改后复检（风险差值 / 事实保全 / 节奏回归） | python-docx |

```bash
python scripts/aigc_detox_lcw_scan.py scan a.docx --out scan.json
python scripts/aigc_detox_lcw_scan.py report scan.json results.json --out-dir report/
python scripts/aigc_detox_lcw_rewrite.py dry-run a.docx repl.json
python scripts/aigc_detox_lcw_rewrite.py apply  a.docx repl.json --out a-new.docx --track-changes
python scripts/aigc_detox_lcw_compare.py a.docx a-new.docx --json diff.json
```

> `report` 的前两个参数是**位置参数**（scan JSON、助手判读 JSON），输出目录用 `--out-dir`。
> `features` 接受 DOCX 路径、文本文件路径或字面文本三种输入，返回体里的 `source`
> 字段会说明它实际按哪种方式读的 —— 若 `source` 仍是 `text` 而你传的是路径，说明路径未被识别。

**环境要求**：Python 3.9+，`python-docx`（必需）、`reportlab`（出 PDF 时才要）。
不需要 LibreOffice、不需要 Word 自动化、不需要联网。

---

## 9. 详细材料

- `references/benchmark.md` —— 6 道对抗测试的完整结果、五家评分矩阵、每个取舍的依据
- `references/patterns.md` —— 16 种 AI 写作模式的详细判据与改写前后对照
- `references/signals.md` —— 脚本各个信号的具体正则与阈值
- `references/report_format.md` —— HTML/PDF 报告版式

---

## 10. 出处与署名

### 致谢（本项目的思路来源）

作者署名 `lcw`，已写在 skill 名与全部脚本文件名上（`aigc-detox-lcw`、`aigc_detox_lcw_*.py`）。
但**方法论和灵感属于下面五位作者**——他们把自己的工作以 MIT 许可公开，才使这个工具成为可能。
任何情况下使用或再分发本工具，请连同这份名单一起保留。

| 作者 | 项目 | 学到了什么 | ⭐ |
|:--|:--|:--|--:|
| **[@ZyhSechub](https://github.com/ZyhSechub)** | [chinese-thesis-workbench-skill](https://github.com/ZyhSechub/chinese-thesis-workbench-skill) | 报告优先、留痕可追溯，以及**「不承诺绕过任何检测器」的边界**——本工具第 1 条前提由此而来。其检测器实测误差 7/6 题，已弃用 | 594 |
| **[@redbaronyyyyy-eng](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic)** | [humanizer-zh-academic](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic) | **16 种 AI 写作模式判据**、改写前后对照写法、文体标定、噪声保留原则——方法论主体 | 349 |
| **[@HoneyMeta](https://github.com/HoneyMeta/ai-check-skills)** | [ai-check-skills](https://github.com/HoneyMeta/ai-check-skills) | **脚本不算分、只给确定性信号，判断权交回人和模型**；数字引用零丢失护栏；风险/缓解**双向**抗误报设计——检测引擎与改写护栏来源 | 32 |
| **[@free-revalution](https://github.com/free-revalution/AIGC-Detector-Pro)** | [AIGC-Detector-Pro](https://github.com/free-revalution/AIGC-Detector-Pro) | **五维语义诊断**的维度划分。打分制换模型就变、不可复现，故只借维度不借分数 | 157 |
| **[@Yezery](https://github.com/Yezery/aigc-down-skill)** | [aigc-down-skill](https://github.com/Yezery/aigc-down-skill) | 同源平行实现（相似度 76%），展示同一套判据的不同落地顺序；留档未并入 | 252 |

另谢 **[@Thundercup](https://github.com/Thundercup)** 对 AIGC-Detector-Pro 的贡献。

### 采用与弃用明细

上表为「学到了什么」，下表为「代码/文本层面具体采用了什么」：

| 前身 | 采用的 | 许可证 |
|---|---|---|
| [ai-check](https://github.com/HoneyMeta/ai-check-skills) | 检测引擎口径、改写护栏（引用/数字零丢失）、DOCX 原地改写与修订痕迹、HTML/PDF 报告骨架 | MIT |
| [humanizer-zh-academic](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic) | 16 种 AI 写作模式判据、改写前后对照示例、文体标定、噪声保留原则 | MIT |
| [aigc-detector](https://github.com/free-revalution/AIGC-Detector-Pro) | 五维语义诊断的**维度名称**（分数制不采用，理由见 benchmark §四） | MIT |
| [chinese-thesis-workbench](https://github.com/ZyhSechub/chinese-thesis-workbench-skill) | 未并入代码，仅作流程对照与边界表述来源；其检测器误差 7/6 题，已弃用 | MIT |
| [aigc-down-skill](https://github.com/Yezery/aigc-down-skill) | 未并入正文（与 humanizer 同血缘，相似度 76%），留档备份 | MIT |

五位作者均为 MIT 许可，原始版权声明与署名完整保留在 `LICENSE` 中。

**本次新增、五个前身都没有的第一个环节**：改写后复检闭环（`aigc_detox_lcw_compare.py`）。
五个前身全部是「扫描 → 改写 → 结束」，没有一家在改完后重新验证。复检器比对风险信号、
缓解信号、句子节奏，以及引用与数字是否丢失，并对「改完反而更整齐」这种隐性退化报警。

**第二个新增环节**：小句节奏盲区补丁（`aigc_detox_lcw_scan.py` 的 `clause_rhythm_features`）。
用 PaperPass 标红版反推出的结构性漏洞——句级节奏检查要求 ≥4 句，而中文长段落常只有 2–3 句，
这部分从未被检查。补丁在句级沉默时回退到小句级，召回 18.2% → 31.8%，误报 0% → 4.5%，
六道基准题零变化。
