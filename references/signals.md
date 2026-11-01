# signals.md —— 脚本里到底在算什么

本文件说明 `aigc_detox_lcw_scan.py` 的每一个信号：**触发条件、正则原文、阈值、为什么这么定**。
它存在的目的是：当用户问"你为什么说这段有风险"，你能指出具体是哪条规则命中的，而不是说"我感觉像"。

> 所有阈值都是**机械阈值**，同一份文本跑两次结果必然相同。
> 这一点前身 aigc-detector 做不到——它的分数是模型读完主观给的。
> 详见 `benchmark.md`。

---

## 一、句子切分（一切信号的底座）

```python
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])\s*|(?<=[.])\s+(?=[A-Z0-9\"“(\[])")
```

- 中文按 `。！？；` 切；英文按 `.` 后跟空格 + 大写/数字/引号/括号切
- **长度 > 5 个非空白字符**的片段才算一句（`count_chars(item) > 5`）
- `count_chars(text) = len(re.sub(r"\s+", "", text))` —— **去掉所有空白再数**
- 中英混排时不需要切换规则：中文一句 25 字，英文一句 80 字母，变异系数把量纲吃掉了

> **踩过的坑（真事）**：测试语料第一行带了个标题「T3 隐身 AI（期望 high）」，
> 被当成正文句子计入，T3 的 CV 从 0.064 被抬到 0.337，直接导致结论反转。
> **喂给脚本的文本必须是纯正文**，不要带任何标注、编号、期望值。

---

## 二、句长变异系数 CV（本工具最有价值的一维）

```python
sentence_lengths = [count_chars(s) for s in sentences]
avg = sum(sentence_lengths) / len(sentence_lengths)
variance = sum((x - avg) ** 2 for x in sentence_lengths) / len(sentence_lengths)
cv = math.sqrt(variance) / avg if avg else None
uniform = len(sentences) >= 4 and cv is not None and cv < 0.3
```

| 条件 | 判定 |
|---|---|
| 句数 ≥ 4 且 CV < **0.30** | 触发风险信号「句式节奏过于均匀」 |
| 句数 < 4 | **不判**（样本不够，任何 CV 都无意义） |
| CV ≥ 0.30 | 不触发 |

**为什么用变异系数而不是方差**：方差带量纲。中文句子 25 字、英文句子 80 字母，
同一段文本换个语言方差就变了，阈值必须跟着变。
除以均值之后变成无量纲比例，**一条规则同时管中英文**。

**实测基准值**（干净文本，无标题行）：

| 文本 | CV | 性质 |
|---|---|---|
| T3 隐身 AI（零模板词，8 句 24–30 字） | **0.064** | 机器味最重 |
| T5 英文 LLM 腔 | 0.172 | 机器味重 |
| T6 有"综上所述"但数据扎实 | 0.334 | 人味 |
| T4 引用实验密集 | 0.383 | 人味 |
| T2 真人写作 | 0.396 | 人味 |
| T1 满配模板 AI | 0.402 | **CV 高但仍该判 AI** |

> **注意最后一行**：T1 是满配模板 AI，CV 却有 0.402。
> **CV 单独用会漏掉"模板词堆满但句长参差"的 AI**。
> 这就是为什么必须三层诊断——第一层管 T1，第二层管 T3，谁也替代不了谁。

---

## 三、风险信号（7 类，全部列出来）

### 3.1 模板表达（`TEMPLATE_PATTERNS`，共 22 条）

命中即产出 `模板表达:<标签>`。标签原样列在下面，可直接回报给用户。

**中文 16 条**

| 标签 | 正则 |
|---|---|
| 首先其次最后模板 | `首先[\s\S]{0,120}其次[\s\S]{0,120}(?:最后\|最终)` |
| 一是二是三是罗列 | `一是[\s\S]{0,120}二是[\s\S]{0,120}三是` |
| 此外同时另外堆叠 | `此外[\s\S]{0,120}同时[\s\S]{0,120}另外` |
| 一方面另一方面对称句 | `一方面[\s\S]{0,120}另一方面` |
| 不仅而且对称句 | `不仅[\s\S]{0,120}(?:而且\|更\|还\|也)` |
| 综上所述 | `综上所述` |
| 总而言之类收束 | `总而言之\|总的来说\|综合来看\|简而言之` |
| 由此可见 | `由此可见` |
| 值得注意的是 | `值得(?:注意\|一提\|关注)的是\|需要指出的是\|不难发现` |
| 不可否认 | `不可否认` |
| 毋庸置疑 | `毋庸置疑` |
| 显而易见 | `显而易见` |
| 众所周知 | `众所周知` |
| 不言而喻 | `不言而喻` |
| 随着发展开头 | `随着.{0,24}?的?(?:快速\|飞速\|迅猛\|迅速\|不断\|持续\|蓬勃)发展` |
| 背景浪潮套语 | `在.{0,20}?(?:大背景\|背景\|浪潮\|时代)下` |

**英文 6 条**（`re.I`）

| 标签 | 正则 |
|---|---|
| In conclusion/summary | `\b(?:in conclusion\|in summary\|to sum up\|all in all)\b` |
| It is worth noting | `\bit is (?:worth noting\|important to note\|noteworthy) that\b` |
| not only…but also | `\bnot only\b[\s\S]{0,120}\bbut also\b` |
| Firstly/Secondly/Finally | `\bfirst(?:ly)?,[\s\S]{0,240}\bsecond(?:ly)?,[\s\S]{0,240}\b(?:finally\|lastly\|third(?:ly)?),` |
| In today's… opener | `\bin (?:today's\|the modern\|an era of\|the rapidly evolving\|the ever-evolving)\b` |

> 注意「一方面…另一方面」这类**对称句只要两项就触发**，不要求三项。
> 早期版本只抓三元并列，结果两项对称全放过去了。

### 3.2 句式节奏过于均匀

见上文 §二。触发串：`句式节奏过于均匀`。

### 3.2b 小句节奏过于均匀（句级检查的盲区补丁）

句级检查要求 `句数 >= 4`，但**中文学术段落经常只有 2–3 个句号**——这类段落句级
检查根本不运行，等于漏检。补丁只在这块盲区里启用，另报一个独立标签，不覆盖、
不改写任何既有判定：

```python
def clause_rhythm_features(text):
    sentences = split_sentences(text)
    if not 2 <= len(sentences) <= 3:      # 句级检查能看见的，不归我管
        return False
    if count_chars(text) < 150:            # 太短的段落没有节奏可言
        return False
    if cjk_chars < ascii_letters:          # 只治中文；英文小句按字符计数尺度不同
        return False
    lengths = [count_chars(c) for c in split_clauses(text)]   # 按 ，、；。：！？ 切
    if len(lengths) < 8:                   # 小句少于 8 个，样本不够
        return False
    clause_cv = sqrt(variance(lengths)) / mean(lengths)
    return clause_cv < 0.45
```

触发串：`小句节奏过于均匀`。

**实测（以 PaperPass 标红版为标签语料，257 段）**

| 指标 | 句级检查 | 加上小句补丁 |
|---|---|---|
| 标红段落召回 | 18.2%（8/44） | **31.8%**（14/44） |
| 未标红段落误报 | 0%（0/22） | 4.5%（1/22） |
| 六道基准题 T1–T6 | — | **完全无变化** |
| 清稿触发段数 | 3/37 | 4/37 |

多抓的 6 段（idx 11/13/128/150/177/237，clause_cv 0.34–0.42）全都是原先句级检查
看不见的长段落。漏抓仍有 10 段，**这不是万能补丁，只是把盲区缩小**。

**为什么只做增量而不替换**：把 `clause_cv` 拿去替代句级 CV 时，召回能到 50%，
但清稿误报飙到 32.4%——那等于用准确率换召回，不可接受。补丁版本永远只在句级
检查沉默时才发言，所以它不可能压制任何已有信号。

---

### 3.3 连接词密集

```python
connector_count = sum(text.count(c) for c in CONNECTORS) + len(EN_CONNECTOR_RE.findall(text))
connector_density = round(connector_count / len(sentences), 3)
触发条件: connector_density >= 0.45 AND connector_count >= 3
```

**中文连接词 15 个**：因此 / 然而 / 同时 / 此外 / 另外 / 由此可见 / 综上 / 进一步 / 相较之下 / 具体而言 / 首先 / 其次 / 最后 / 一方面 / 另一方面

**英文连接词正则**：`\b(?:moreover|furthermore|additionally|in addition|however|therefore|consequently|thus|hence|nevertheless|notably|importantly|overall|specifically)\b`

**两个条件必须同时满足**。只满足密度不满足个数时（比如一段只有 2 句但塞了 2 个连接词，密度 1.0），
不判密集——那样会把短段落冤枉成 AI。

### 3.4 破折号偏多

```python
dash_count = text.count("——") + len(re.findall(r"(?<!—)—(?!—)", text))
触发条件: dash_count >= 2
```

`——` 算一次，独立的 `—`（前后不是 `—`）也算一次，避免把 `————` 数成 4 次。

### 3.5 泛化套话（`GENERIC_CLAIM_PATTERNS`，共 13 条）

产出 `泛化套话:<前3个标签>`，`genericClaimCount` 是**所有模式命中次数的总和**。

| 标签 | 正则 |
|---|---|
| 重要意义套话 | `(?:具有\|具备).{0,12}(?:重要\|重大).{0,12}(?:意义\|价值)` |
| 广阔前景套话 | `(?:广阔\|良好).{0,8}(?:应用)?前景\|前景(?:十分\|非常)?广阔` |
| 理论实践价值套话 | `理论价值.{0,12}现实意义\|现实意义.{0,12}理论价值` |
| 高效可靠可信泛化目标 | `(?:高效\|可靠\|可信\|智能化\|实用化).{0,18}(?:系统\|框架\|方案)` |
| 深入全面研究 | `(?:深入\|全面).{0,8}研究` |
| 一系列问题挑战 | `一系列.{0,8}(?:问题\|挑战)` |
| 赋能助力流行语 | `赋能\|助力\|深度融合\|全方位\|多维度\|新范式\|新路径\|新思路` |
| 关键作用套话 | `发挥(?:着)?.{0,6}(?:重要\|关键\|不可替代\|积极)(?:的)?作用\|至关重要\|举足轻重` |
| 支撑基础套话 | `(?:提供\|奠定)(?:了)?.{0,6}(?:有力\|坚实\|重要)(?:的)?(?:支撑\|基础\|保障)` |
| 日益凸显套话 | `日益(?:增长\|突出\|凸显\|重要\|广泛\|迫切)\|愈发(?:重要\|突出)` |
| LLM 高频词 | `\b(?:delve[sd]?\|delving\|tapestry\|testament to\|pivotal\|underscor(?:e\|es\|ed\|ing)\|showcas(?:e\|es\|ed\|ing)\|intricate\|multifaceted\|realm\|seamless(?:ly)?\|cutting-edge\|ever-evolving\|paving the way\|shed(?:s\|ding)? light on\|navigat(?:e\|es\|ing) the complexities\|game[- ]changer)\b` |
| crucial role | `\bplay(?:s\|ing)? an? (?:crucial\|pivotal\|vital\|key\|significant\|important) role\b` |
| significant implications | `\b(?:significant\|profound\|far-reaching) (?:implications\|potential)\b\|\bbroad (?:application )?prospects\b` |

### 3.6 贡献罗列结构

```python
主要研究工作如下 | 具体研究内容如下
| 本文(?:提出|构建|设计).{0,80}(?:方法|框架).{0,80}(?:实验结果|结果表明)
| \b(?:our|the main) contributions (?:are|of this (?:paper|work))\b   (re.I)
```

### 3.7 目标表述泛化

```python
(?:旨在|力求|致力于).{0,40}(?:高效|可靠|可信|智能化|实用化)
```

---

## 四、缓解信号（4 类，抗误报的核心）

**这一组是本工具区别于前身的最重要部分。**
chinese-thesis-workbench 的检测器只有风险项、没有缓解项，实测把一篇写着
`92.7%` / `n=1200` / `[12]` 的硬核论文也判出风险（误差 7）。加了这 4 类之后误差降到 1。

### 4.1 具体证据（`EVIDENCE_MARKER_PATTERNS`，6 条）

| 标签 | 正则要点 |
|---|---|
| 引用编号 | `\[\d+(?:\s*[-–,，、]\s*\d+)*\]` 或 `\([A-Z][A-Za-z-]+(?: et al\.)?,? \d{4}[a-z]?\)` |
| 实验指标 | `\d+(?:\.\d+)?\s*(?:%\|％\|G\s*FLOPs?\|FLOPs?\|MB\|GB\|ms\|s\|Hz\|kHz\|MHz\|dB\|mAP\|AUC\|F1\|BLEU\|ROUGE\|mIoU\|PSNR\|SSIM)(?![A-Za-z])` |
| 统计量 | `\bp\s*[<=>≤]\s*0?\.\d+\|±\|95\s*%\s*CI\|\bn\s*=\s*\d+\|标准差\|置信区间` |
| 模型或方法名 | 见 §4.2 |
| 实验结果表述 | `实验结果(?:表明\|显示\|验证)\|准确率\|召回率\|计算复杂度\|消融\|对比实验\|数据集\|\b(?:ablation\|baseline\|dataset\|benchmark)s?\b` |
| 限定或取舍 | `在.{0,18}(?:条件\|场景\|约束\|限制)下\|针对.{0,24}(?:问题\|场景\|任务)\|本文(?:聚焦\|采用\|选取\|限定)\|\b(?:under the (?:condition\|assumption)\|limited to\|we (?:restrict\|focus on\|chose\|choose\|adopt))\b` |

### 4.2 领域方法细节（`METHOD_NAME_RE`）

```python
\b(?:CNN|RNN|LSTM|GRU|Transformer|BERT|GPT-?\d*|ResNet-?\d*|U-?Net|YOLO\w*|ViT|Grad-CAM|XGBoost|SVM|CQT|MFCC|
BSCQT|DCAM|DCAMNet|AB-CQT|DFAM|DFAMNet)\b
| \b(?=[A-Za-z0-9-]{3,}\b)[A-Z][A-Za-z]*[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)?\b
```

第一段是固定名单，第二段是**通用驼峰/缩写识别**（≥3 字符、至少两个大写），
所以 `BiLSTM`、`EfficientNet-B0`、`LoRA`、`ResNet` 都能自动抓到，不必维护名单。

**触发缓解的条件是 `len(method_names) >= 2`** —— 出现两个**不同**的方法名才算。
只提一个模型名，说明不了这是真人写的。

### 4.3 定量结果支撑

```python
re.search(r"\d+(?:\.\d+)?\s*[%％]", text)
AND
re.search(r"准确率|提升|降低|复杂度|FLOPs?|\b(?:improv|reduc|outperform|accuracy)", text, re.I)
```

**必须同时有百分数**和**有意义的结果词**。
光有 `3.2%` 不算——可能只是"增长了 3.2%"。要配合"准确率/提升/降低"这类才算实证。

### 4.4 限制条件说明

```python
re.search(r"(?:但|然而|不过).{0,40}(?:限制|不足|难以|约束|挑战)", text)
OR
re.search(r"\b(?:however|but|although)\b.{0,80}\b(?:limit(?:ation|ed|s)?|cannot|fails?|constraints?|drawbacks?)\b", text, re.I)
```

**承认局限是最强的人味信号。** 见过太多"只讲成功不讲边界"的 AI 文。

---

## 五、TraceFeatures 输出字段

每个 chunk 的 `traceFeatures` 包含：

```json
{
  "riskSignals": ["模板表达:综上所述", "泛化套话:重要意义套话"],
  "mitigatingSignals": ["具体证据:引用编号", "具体证据:实验指标", "领域方法细节"],
  "templatePhrases": ["综上所述", "值得注意的是"],
  "connectorCount": 3,
  "connectorDensity": 0.375,
  "sentenceCount": 8,
  "sentenceLengthVariance": 132.25,
  "sentenceLengthCV": 0.534,
  "uniformSentenceRhythm": false,
  "genericClaimCount": 3,
  "evidenceMarkers": ["引用编号", "实验指标"]
}
```

---

## 六、怎么读这组数（实操判读）

**不要看信号总数的绝对值，看风险与缓解的对抗关系。**

| 情形 | 判断 | 动作 |
|---|---|---|
| 风险多、缓解 0 | 大概率是 AI 或人肉套模板 | 改 |
| 风险多、缓解 ≥ 3 | 硬核论文只是语言偏官方 | **慎重**，只改模板词，不动内容 |
| 风险少、缓解 0、CV < 0.3 | 隐身 AI 或人写的流水账 | 看内容：有具体事实就是人写的流水账，别动节奏 |
| 风险少、缓解多 | 明显是人写的 | **不要改** |
| 风险 0、缓解 0、CV 正常 | 中性文本 | 不改 |

> 最后一列那个"别动节奏"很重要。**真人也会写出句长均匀的段落**（比如一条条列流程的人）。
> CV 低只是"值得看一眼"，不是"一定是 AI"。要看内容有没有具体事实。

---

## 七、复检器（`aigc_detox_lcw_compare.py`）的三个口径

```bash
python scripts/aigc_detox_lcw_compare.py before.docx after.docx
```

1. **风险差值**：`delta = after_count - before_count`，负数是降了。
   同时给出 `fixed`（改前有改后无）、`kept`（两次都有）、`introduced`（改前无改后**新出现**）。
   `introduced` 非空是危险信号——你把旧毛病改掉，又造了新毛病。
2. **节奏回归**：`regression` = 源 CV ≥ 0.30 而改后 CV < 0.30（源正常、被改平了）。
   `flattened` = `after_cv < before_cv * 0.6`（被压掉六成以上）。
   源本来就 < 0.30 时仍低**不算回归**。
3. **事实保全**：用与改写器同一套 `CITATION_RE` / 数字抽取比对，
   输出 `lostCitations` / `lostNumbers` / `addedCitations` / `addedNumbers`。
   `lost*` 非空 → **FAIL**，不管别的多好看。

**判定优先级**：丢事实（FAIL）> 风险未降/新增风险/节奏回归（WARN）> PASS。
退出码 PASS=0，其余 1，可以直接在 shell 里 `if`。
