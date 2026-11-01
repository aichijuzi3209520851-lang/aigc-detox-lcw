# aigc-detox-lcw

**论文去 AI 味三件套：体检 · 改写 · 复查**

一个给中文（也支持英文）学术写作降 AI 味的 Agent Skill。不是检测器，不承诺绕过任何平台的检测；
它做的是把文本里那些「一看就是机器写的」的统计特征找出来、改掉，然后**再验证一遍确实改好了**。

> 署名 `lcw`。站在五个 MIT 开源实现上，只取经实测验证过的部分——取舍依据全部公开在
> [`references/benchmark.md`](references/benchmark.md)。

---

## 致谢

**这个项目不是从零开始的。**

它的骨架、判据、工具链，来自下面五位作者公开发布、以 MIT 许可开放的工作。我做的是把它们逐项实测、
择优缝合，再补上两个它们都缺的环节。但**思路和灵感是他们的**，这份名单理应放在最显眼的位置，
而不是塞在文件末尾。

| 作者 | 项目 | 我从他们那里学到了什么 | ⭐ |
|:--|:--|:--|--:|
| **[@ZyhSechub](https://github.com/ZyhSechub)** | [chinese-thesis-workbench-skill](https://github.com/ZyhSechub/chinese-thesis-workbench-skill) | 论文交付要留痕、可追溯：状态机、质量闸门、**报告优先**（先出诊断再动笔）。它的检测器我实测后弃用了（6 道对抗题误差 7），但「不承诺绕过任何检测器」这条边界正是从它这里学来的——我把它变成了本项目的第 1 条前提。 | 594 |
| **[@redbaronyyyyy-eng](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic)** | [humanizer-zh-academic](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic) | **16 种 AI 写作模式的分类框架**、每一模式「改写前 → 改写后」的对照写法、文体标定表，以及「噪声保留」（别改到 100% 干净，留 2–3 处自然噪声）。本项目方法论层的主体来自这里。 | 349 |
| **[@HoneyMeta](https://github.com/HoneyMeta/ai-check-skills)** | [ai-check-skills](https://github.com/HoneyMeta/ai-check-skills) | 最关键的一条设计哲学：**脚本不算分、只给确定性文本信号，判断权交回人和模型**。还有「数字和引用是事实，丢了就拒绝落盘」的护栏，以及风险信号 / 缓解信号**双向**设计的抗误报思路。本项目的检测引擎与改写护栏源自这里。 | 32 |
| **[@free-revalution](https://github.com/free-revalution/AIGC-Detector-Pro)** | [AIGC-Detector-Pro](https://github.com/free-revalution/AIGC-Detector-Pro) | **五维语义诊断**的维度划分：句式规整度 / 逻辑词密度 / 语态特征 / 词汇多样性 / 论证深度。它的打分制我实测后发现换模型就变、不可复现，所以只借维度名不借分数——但它让我第一次意识到「检测」可以拆成多个维度，而不是一张关键词表。 | 157 |
| **[@Yezery](https://github.com/Yezery/aigc-down-skill)** | [aigc-down-skill](https://github.com/Yezery/aigc-down-skill) | 与 humanizer 同源（相似度 76%）的平行实现。它更细的模式判定细则，以及「先提取待改内容、再改」的四步流程，让我看到**同一套判据可以有不同的落地顺序**。作为备份留档，未并入正文。 | 252 |

另感谢 **[@Thundercup](https://github.com/Thundercup)** 对 AIGC-Detector-Pro 的贡献。

没有这几位把方法论公开写出来，这个仓库不会存在。如果上述任何一位认为此处致谢或署名方式不妥、
或希望调整引用形式，**请开 issue，我会立即修改**。

---

## 它解决什么问题

AI 写的文本有两个层次的问题：

1. **表层**——模板套话。「综上所述」「值得注意的是」「首先/其次/再次」「具有重要意义」。
   这些用正则能抓，市面上大多数工具停在这一层。
2. **深层**——节奏同质。每句话长度都在 20–30 字之间，每句都是「[对象]+[做什么]+[为什么]」的同构骨架，
   一个模板词都没有。**没有任何关键词可以匹配，只能看句长分布。**

第二层才是真正难的部分。这个项目在真实论文上量过：一份 PaperPass 判红 44 段的毕业论文里，
有 28 段一个模板词都没有；而句长变异系数（CV）在这批段落上是 0.378，人写的是 0.503——
**AUC 只有 0.502，等于抛硬币**。所以只加「节奏」这一条也远远不够，必须三层一起上。

---

## 三层诊断

| 层 | 谁给的 | 看什么 |
|---|---|---|
| 第一层：词面 | 脚本 | 22 条模板正则、13 条泛化套话正则、连接词密度、破折号密度 |
| 第二层：节奏 | 脚本 | 句长变异系数 CV。`CV < 0.30` 且句数 ≥ 4 = 过于均匀；`0.30–0.45` 正常不动；`> 0.45` 是人味，不要改 |
| 第二层补丁：小句节奏 | 脚本 | 中文长段落常只有 2–3 句，句级检查根本不会运行。此时回退到小句级（按逗号切），`clause_cv < 0.45` 触发 |
| 第三层：语义 | 模型 | 五维度描述（句式规整度 / 逻辑词密度 / 语态特征 / 词汇多样性 / 论证深度）——**只描述，不打分** |

**为什么第三层不打分**：分数换一个模型、换一个温度就变，不可复现。一句「AIGC 风险 77.3%」
看着精确，实际上没有任何可验证的含义。所以这里只给判断依据，把判断权交回人手上。

**抗误报同样重要**。光找风险信号会让所有技术论文都中招——引用密集、术语密集、结构整齐
本来就是学术写作的正常样子。所以脚本同时算 4 类**缓解信号**：具体证据、领域方法细节（≥2 个模型名）、
定量结果支撑（同时有百分比和准确率类词）、限制条件说明。风险多而缓解信号 ≥3 的段落，
结论是「只改词，不要动内容」。

---

## 三个脚本

| 脚本 | 作用 |
|---|---|
| `scripts/aigc_detox_lcw_scan.py` | `scan` DOCX → chunk + 机械信号；`report` 出 HTML/PDF 报告；`features` 查任意文本或文件 |
| `scripts/aigc_detox_lcw_rewrite.py` | `dry-run` 预检 / `apply` 写出新 DOCX，可选生成 Word 修订痕迹 |
| `scripts/aigc_detox_lcw_compare.py` | **改前改后复检**（这是五个前身都没有的环节） |

```bash
# 1. 体检
python scripts/aigc_detox_lcw_scan.py scan 论文.docx --out scan.json
python scripts/aigc_detox_lcw_scan.py report scan.json results.json --out-dir report/

# 2. 改写（先预检，全绿再落盘）
python scripts/aigc_detox_lcw_rewrite.py dry-run 论文.docx repl.json
python scripts/aigc_detox_lcw_rewrite.py apply  论文.docx repl.json --out 论文-改后.docx --track-changes

# 3. 复查
python scripts/aigc_detox_lcw_compare.py 论文.docx 论文-改后.docx --json diff.json
```

`compare` 的退出码：`0` = PASS，`1` = WARN 或 FAIL，可直接接进 CI。

### 两道硬护栏

改写脚本会**拒绝执行**下面两种情况，不是提醒，是不写盘：

- **丢引用标记**：源文本有 `[12]`、`[13,14]`，替换文本里没有 → `missing citation marks: [12]`
- **丢数字**：源文本有 `92.7`、`3.2`，替换文本里没有 → `missing numbers: 92.7, 3.2`

数字是事实。改文风可以，改数据是学术事故。要破例必须显式写 `"allowNumberChange": true`
——这个开关存在的意义是让你意识到自己在干什么，不是让你方便。

---

## 复检器抓得到什么

这是本项目和同类工具最大的差别。真实案例：一次看起来非常成功的改写——

| 指标 | 改前 | 改后 |
|---|---|---|
| 风险信号 | 6 | 0 ✅ |
| 模板短语 | 5 | 0 ✅ |
| 泛化套话 | 1 | 0 ✅ |
| 丢失引用 | — | 无 ✅ |
| 丢失数字 | — | 无 ✅ |
| **句长 CV** | 0.831 | **0.951** |

风险全清零、事实零丢失，但它同时会告你：**有没有把文本从一种机器味改成另一种机器味**。
句长 CV 被压到 `0.30` 以下的改写会被判 **WARN**——模板词是没了，但句子变得一样长了，
换了个姿势还是机器。这个警告只有复检器会给。

---

## 实测数据（不吹）

- **6 道带真值的对抗题**：包含满配模板 AI、真人写作陷阱、**零模板词的隐身 AI**、
  引用密集的真论文、英文 LLM 腔、含「综上所述」但数据扎实的正当总结。
  本引擎误差 1/6（且完全可复现）；同场比较的纯语义判读方案误差 0 但换模型就变，
  其余三个方案误差 5–7。
- **小句节奏补丁**：标注论文召回 18.2% → **31.8%**，误报 0% → 4.5%，六道基准题判定**零变化**。
- **真实论文端到端**：48 段改写，`compare` PASS，正文 15036 → 13994 字，事实零丢失。

完整数据、失败实验（8 轮，包括几个召回率直接归零的方案）和每个取舍的理由都在
[`references/benchmark.md`](references/benchmark.md)。**里面也有我自己犯过的错**——
比如一度把测试文件的标题行混进正文，把 CV 从 0.064 虚抬到 0.337，得出完全相反的结论。

---

## 三条不可越过的前提

1. **这不是检测器**。它给的是「确定性文本信号 + 诊断意见」，不是任何平台的 AIGC 百分点。
   不许说「AI 率 87%」，不许声称对齐知网、维普、Turnitin。
2. **事实是只读的**。数字、引用标记、模型名、指标、结论方向一律不得改动。
3. **不动原文件**。所有改写写入新文件，脚本拒绝 out 与源同名。

---

## 安装

这个目录本身就是 skill 本体（`SKILL.md` + `references/` + `scripts/`）。
把它放到你的 Agent 的 skills 目录下即可：

```bash
# Claude Code / Codex / DSH / TRAE / ZCode / WorkBuddy 等
ln -s /path/to/aigc-detox-lcw ~/.claude/skills/aigc-detox-lcw        # macOS / Linux
# Windows 用 junction（不要用符号链接，跨盘会出问题）
# New-Item -ItemType Junction -Path "$HOME\.claude\skills\aigc-detox-lcw" -Target "D:\path\to\aigc-detox-lcw"
```

已验证可用：`.dsh` / `.agents` / `.claude` / `.codex` / `.trae-cn` / `.zcode` / `.workbuddy`
七个目录（豆包 Doubao 读 `.agents/skills`）。

**环境要求**：Python 3.9+，`python-docx`（必需）、`reportlab`（出 PDF 时才要）。
不需要 LibreOffice、不需要 Word 自动化、不需要联网。

---

## 目录

```
SKILL.md                       主方法论：7 步工作流、9 条硬约束、三层诊断、7 步改写手法
references/
  benchmark.md                 6 道对抗测试、评分矩阵、8 轮失败实验、每个取舍的依据
  patterns.md                  16 种 AI 写作模式的判据与改写前后对照
  signals.md                   脚本各信号的完整正则与阈值
  report_format.md             HTML/PDF 报告版式
scripts/
  aigc_detox_lcw_scan.py       DOCX 扫描 + 报告生成
  aigc_detox_lcw_rewrite.py    带护栏的改写
  aigc_detox_lcw_compare.py    改前改后复检
```

---

## 出处与许可

五个上游项目均为 **MIT**。逐项采用/弃用对照见下方，完整致谢（含作者与学到的具体内容）在文首
[**致谢**](#致谢)一节。

| 前身 | 采用的部分 |
|---|---|
| [ai-check](https://github.com/HoneyMeta/ai-check-skills) | 检测引擎口径、改写护栏、DOCX 改写与修订痕迹、报告骨架 |
| [humanizer-zh-academic](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic) | 16 种写作模式判据、对照示例、文体标定、噪声保留 |
| [aigc-detector](https://github.com/free-revalution/AIGC-Detector-Pro) | 五维诊断的维度名称（分数制不采用） |
| [chinese-thesis-workbench](https://github.com/ZyhSechub/chinese-thesis-workbench-skill) | 「不承诺绕过检测器」的边界与报告优先流程；检测器已弃用（误差 7/6 题） |
| [aigc-down-skill](https://github.com/Yezery/aigc-down-skill) | 未并入（与 humanizer 相似度 76%），留档 |

本次新增、五个前身都没有的：**改写后复检闭环** 与 **小句节奏盲区补丁**。
品牌与「AI 率百分比」措辞已从继承代码中全部清除——本项目的规则禁止它输出那种数字。

MIT，见 [LICENSE](LICENSE)。衍生自上述五个 MIT 项目，**其原始版权声明与作者署名全部保留**。
