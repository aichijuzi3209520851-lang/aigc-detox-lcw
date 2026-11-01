# 安装指南（新手向 · 逐 Agent 版）

> 这份文档假设你**从来没装过 skill**。跟着做就行。
> 全程不需要写代码，只需要「复制路径」和「粘贴一句话」。

---

## 零、先搞清楚三件事

### 1. skill 是什么

一个 skill 就是**一个文件夹**，里面有个 `SKILL.md`。
你的 Agent 每次启动会去几个固定位置扫这个文件，扫到了它就「学会了」这项能力。

`aigc-detox-lcw` 这个文件夹长这样：

```
aigc-detox-lcw/
├── SKILL.md              ← 必须叫这个名字，Agent 靠它认出 skill
├── DISCLAIMER.md         ← 免责声明，装完第一次用会给你看
├── INSTALL.md            ← 你正在看的这份
├── README.md
├── LICENSE
├── references/           ← 方法论细节，Agent 需要时才读
└── scripts/              ← 三个 Python 脚本
```

### 2. 安装 = 把这个文件夹「链」到 Agent 的 skills 目录

不是复制，是**做快捷方式**（术语叫软链接或 junction）。
这样你以后更新这个文件夹，所有 Agent 同步生效，不用挨个重装。

- macOS / Linux：用 `ln -s`（软链接）
- Windows：用 junction（**不要用符号链接**，跨盘会失效，而且要管理员权限）

### 3. 只有两步

**第一步**：把仓库下载到本地，记住它的完整路径。
**第二步**：在你用的 Agent 里，把下面「对应那一节」的提示词**整段复制粘贴**给它，让它自己装。

> 💡 **强烈推荐第二步直接让 Agent 干**。它知道自己的目录在哪，比你手敲命令可靠。
> 下面每个 Agent 都给了**专属提示词**，直接复制。

---

## 一、第一步：拿到本地路径

### 方法 A：用 git（推荐，方便以后更新）

打开终端（Windows 用 PowerShell，macOS 用「终端」），执行：

```bash
cd ~/Documents
git clone https://github.com/aichijuzi3209520851-lang/aigc-detox-lcw.git
```

装好后路径是：
- macOS / Linux：`~/Documents/aigc-detox-lcw`
- Windows：`C:\Users\你的用户名\Documents\aigc-detox-lcw`

### 方法 B：不用 git（下载 zip）

1. 打开 https://github.com/aichijuzi3209520851-lang/aigc-detox-lcw
2. 绿色按钮 **Code** → **Download ZIP**
3. 解压，你会得到一个叫 `aigc-detox-lcw-main` 的文件夹
4. **把它改名成 `aigc-detox-lcw`**（去掉 `-main`，这步很重要，脚本名依赖它）

### 检查一下（可选但建议）

在终端里进到这个目录，跑一句：

```bash
python scripts/aigc_detox_lcw_scan.py features "综上所述，值得注意的是，这具有重要意义。"
```

看到类似 `"riskSignals": ["模板表达:综上所述", ...]` 就说明**环境没问题**。
如果报 `No module named 'docx'`，执行 `pip install python-docx`。

> **环境要求**：Python 3.9+；`python-docx`（必需）；`reportlab`（要出 PDF 才需要，`pip install reportlab`）。
> 不需要 LibreOffice、不需要装 Word、不需要联网。

---

## 二、第二步：按你的 Agent 安装

先找你的 Agent 是哪一行：

| 你用的是 | 看第几节 |
|:--|:--|
| **豆包 Doubao** | 2.1 |
| **WorkBuddy** | 2.2 |
| **TRAE** | 2.3 |
| **ZCode** | 2.4 |
| **OpenCode** | 2.5 |
| **Codex (OpenAI)** | 2.6 |
| **Claude Code** | 2.7 |
| **DSH (DeepSeek Harness)** | 2.8 |
| **Cursor / 通义灵码 / 其他** | 2.9 |

---

### 2.1 豆包 Doubao

**它的 skill 目录**：`~/.agents/skills`（这是豆包的一等公民默认目录，不需要配置）

**你要做的**：把这个提示词整段复制给豆包。

```
我有一个本地 skill 文件夹，想让你装到你能读到 skill 的目录里，这样以后我让你
"降低AI率/去AI味/降AIGC"时你能直接调用。

skill 源路径：<这里换成你的实际路径，例如 D:\Documents\aigc-detox-lcw>
目标目录：C:\Users\<你的用户名>\.agents\skills\aigc-detox-lcw

请帮我：
1. 先确认源目录里有 SKILL.md（读一下第一行的 name: 字段，应该是 aigc-detox-lcw）
2. 如果目标目录不存在就创建它
3. 建一个链接（Windows 用 junction，命令：
   New-Item -ItemType Junction -Path "<目标路径>" -Target "<源路径>"
   macOS/Linux 用：ln -s "<源路径>" "<目标路径>"）
   —— 不要用符号链接，Windows 上跨盘会失效
4. 建完后读一下目标路径下的 SKILL.md，确认能读到、name 字段正确
5. 把结果告诉我：成功还是失败、失败在哪一步

装好后，如果你能在技能列表里看到 aigc-detox-lcw，就说明成功了。
另外请把 DISCLAIMER.md 完整念给我听一遍，我要确认我知道使用限制。
```

---

### 2.2 WorkBuddy

**它的 skill 目录**：`~/.workbuddy/skills`

```
我有一个本地 skill 文件夹，想让你装到 WorkBuddy 的 skill 目录里。

skill 源路径：<换成你的实际路径>
目标目录：C:\Users\<你的用户名>\.workbuddy\skills\aigc-detox-lcw

请帮我：
1. 确认源目录里有 SKILL.md，读一下 name: 字段（应该是 aigc-detox-lcw）
2. 目标目录不存在就创建
3. Windows 建 junction（不要符号链接）：
   New-Item -ItemType Junction -Path "<目标路径>" -Target "<源路径>"
   macOS/Linux：ln -s "<源路径>" "<目标路径>"
4. 验证：读目标路径下的 SKILL.md，确认可读且 name 正确
5. 告诉我结果

装好后把 DISCLAIMER.md 完整念给我听一遍。
```

---

### 2.3 TRAE（国内版 / 国际版）

**它的 skill 目录**：
- 国内版 TRAE CN：`~/.trae-cn/skills`
- 国际版 TRAE：`~/.trae/skills`

> 不确定自己是哪个版？让 TRAE 自己查：它知道自己的目录。

```
我有一个本地 skill 文件夹要装到 TRAE。

skill 源路径：<换成你的实际路径>

请你先自己判断我是国内版还是国际版：
- 国内版的 skill 目录是 C:\Users\<用户名>\.trae-cn\skills
- 国际版的 skill 目录是 C:\Users\<用户名>\.trae\skills
你可以检查哪个目录已经存在，来判断。

然后：
1. 确认源目录里有 SKILL.md（name: 应为 aigc-detox-lcw）
2. 在正确的目录下建链接：<正确目录>\aigc-detox-lcw
   Windows 用 New-Item -ItemType Junction（不要符号链接）
   macOS/Linux 用 ln -s
3. 验证目标路径下 SKILL.md 可读、name 正确
4. 告诉我装到了哪个目录、成功与否

注意：TRAE 目录扫描不依赖注册文件，建好链接就能被识别，不需要改 skill-config.json。
装好后把 DISCLAIMER.md 完整念给我听。
```

---

### 2.4 ZCode

**它的 skill 目录**：`~/.zcode/skills`（注意：这个目录可能一开始不存在，需要新建）

```
我有一个本地 skill 文件夹要装到 ZCode。

skill 源路径：<换成你的实际路径>
目标目录：C:\Users\<用户名>\.zcode\skills\aigc-detox-lcw

请帮我：
1. 确认源目录里有 SKILL.md，name: 应为 aigc-detox-lcw
2. ~/.zcode/skills 这个目录可能还不存在（ZCode 桌面版默认没建），
   不存在就创建：New-Item -ItemType Directory -Force -Path "C:\Users\<用户名>\.zcode\skills"
3. 建 junction（不要符号链接）：
   New-Item -ItemType Junction -Path "<目标>\aigc-detox-lcw" -Target "<源路径>"
4. 验证：读目标路径下 SKILL.md，确认 name 正确
5. 报告结果

装好后把 DISCLAIMER.md 完整念给我听。
```

---

### 2.5 OpenCode

**它的 skill 目录**（按官方文档，四选一都行，推荐第 1 个）：
1. 全局：`~/.config/opencode/skills/<name>/SKILL.md` ← **推荐**
2. 项目级：`.opencode/skills/<name>/SKILL.md`
3. 兼容 Claude：`~/.claude/skills/` 或 `.claude/skills/`
4. 兼容通用：`~/.agents/skills/` 或 `.agents/skills/`

> 结构要求：**一个 skill 一个文件夹，文件夹名必须等于 SKILL.md 里的 name 字段。**

```
我有一个本地 skill 文件夹要装到 OpenCode。

skill 源路径：<换成你的实际路径>
目标目录：~/.config/opencode/skills/aigc-detox-lcw
（Windows 上是 C:\Users\<用户名>\.config\opencode\skills\aigc-detox-lcw）

请帮我：
1. 确认源目录里有 SKILL.md，name: 应为 aigc-detox-lcw
   （OpenCode 要求文件夹名和 name 字段一致，请核对）
2. 创建父目录（不存在的话）
3. 建链接：
   Windows: New-Item -ItemType Junction -Path "<目标>" -Target "<源路径>"
   macOS/Linux: ln -s "<源路径>" "<目标>"
4. 验证目标路径下 SKILL.md 可读
5. 告诉我结果

注意：OpenCode 同时也读 ~/.claude/skills 和 ~/.agents/skills，
如果你已经在那些地方装过，其实我也能用到，可以告诉我。
装好后把 DISCLAIMER.md 完整念给我听。
```

---

### 2.6 Codex (OpenAI)

**它的 skill 目录**：
- 个人级：`~/.agents/skills`（推荐）
- 项目级：从当前目录一直向上到仓库根，逐层找 `.agents/skills`
- 也兼容 `~/.codex/skills`

```
我有一个本地 skill 文件夹要装到 Codex。

skill 源路径：<换成你的实际路径>
目标目录：C:\Users\<用户名>\.agents\skills\aigc-detox-lcw

请帮我：
1. 确认源目录里有 SKILL.md，name: 应为 aigc-detox-lcw
2. 目标父目录不存在就创建
3. 建 junction（Windows，不要符号链接）/ ln -s（macOS/Linux）
4. 验证可读、name 正确
5. 报告结果

Codex 会从当前目录往上扫 .agents/skills，也会读 ~/.agents/skills，
所以装在个人级目录对所有项目都生效。
装好后把 DISCLAIMER.md 完整念给我听。
```

---

### 2.7 Claude Code

**它的 skill 目录**：
- 个人级：`~/.claude/skills`
- 项目级：`<你的项目>/.claude/skills`

```
我有一个本地 skill 文件夹要装到 Claude Code。

skill 源路径：<换成你的实际路径>
目标目录：C:\Users\<用户名>\.claude\skills\aigc-detox-lcw

请帮我：
1. 确认源目录里有 SKILL.md，name: 应为 aigc-detox-lcw
2. 建链接：
   Windows: New-Item -ItemType Junction -Path "<目标>" -Target "<源路径>"
   macOS/Linux: ln -s "<源路径>" "<目标>"
3. 验证目标路径下 SKILL.md 可读、name 正确
4. 报告结果

装好后把 DISCLAIMER.md 完整念给我听。
```

---

### 2.8 DSH (DeepSeek Harness)

**它的 skill 目录**：`~/.dsh/skills`

```
我有一个本地 skill 文件夹要装到 DSH。

skill 源路径：<换成你的实际路径>
目标目录：C:\Users\<用户名>\.dsh\skills\aigc-detox-lcw

请帮我建 junction（Windows）或软链接（macOS/Linux），然后验证 SKILL.md 可读、
name 字段是 aigc-detox-lcw。装好后把 DISCLAIMER.md 完整念给我听。
```

---

### 2.9 Cursor / 通义灵码 / 其他 Agent

大部分 Agent 现在都兼容下面两个位置之一。**最省事的做法**：装到 `~/.agents/skills`，
这是目前最通用的约定（Codex、OpenCode、ZCode、豆包都读它）。

```
我有一个本地 skill 文件夹，想装到你能读到的通用 skill 目录里。

skill 源路径：<换成你的实际路径>
目标目录：C:\Users\<用户名>\.agents\skills\aigc-detox-lcw

请帮我：
1. 先确认你自己支持从哪里读 skill（查一下你的文档或配置）
2. 如果支持 .agents/skills，就装到那里
3. 建链接（Windows 用 junction，macOS/Linux 用 ln -s）
4. 验证 SKILL.md 可读、name 是 aigc-detox-lcw
5. 告诉我：你支持哪个目录、装到哪了、成功没

重要：不要用符号链接（Windows 上跨盘会失效）。不要复制整个文件夹，要做链接，
这样我更新源目录时你能同步拿到新版。
```

---

## 三、装完之后怎么验证

### 方法一：直接问 Agent

装完后，新开一个对话，问：

```
你现在能用的 skill 列表里，有没有一个叫 aigc-detox-lcw 的？
如果有，把它 SKILL.md 的第一句话读给我听。
```

能读出来 = 装好了。

### 方法二：自己检查链接

在终端里：

```bash
# 看链接是否存在、指向哪里
ls -l ~/.agents/skills/aigc-detox-lcw     # macOS/Linux
dir C:\Users\%USERNAME%\.agents\skills     # Windows
```

Windows 上如果看到 `<JUNCTION>` 或 `<SYMLINKD>`，就说明链上了。

### 方法三：跑一次真实体检

这是最终验证。在终端进到 skill 目录：

```bash
python scripts/aigc_detox_lcw_scan.py scan 你的论文.docx --out scan.json
```

输出里有 `"chunks": N` 和 `"totalChars": N` 就说明**真的能用了**。

---

## 四、常见问题

### Q1：装完了，Agent 说没找到这个 skill

按顺序排查：

1. **目录名对不对**：必须是 `aigc-detox-lcw`，不能是 `aigc-detox-lcw-main`、也不能是 `aigc-detox-lcw-master`
2. **SKILL.md 在不在根目录**：`<skill目录>/SKILL.md`，不能嵌在子目录里
3. **name 字段对不对**：SKILL.md 第一段 frontmatter 里必须有 `name: aigc-detox-lcw`
4. **重启 Agent**：大部分 Agent 是启动时扫目录，装完要重开
5. **路径权限**：Windows 上 junction 目标路径别放在需要管理员权限的地方（比如 `C:\Program Files`）

### Q2：Windows 上建链接报错「权限不足」

用 junction 不需要管理员权限，但如果还是失败：

1. 用 PowerShell（不是 cmd）跑
2. 或者干脆**直接复制文件夹**（放弃自动同步，以后更新要手动重拷）：
   ```powershell
   Copy-Item -Recurse "D:\Documents\aigc-detox-lcw" "C:\Users\$env:USERNAME\.agents\skills\"
   ```

### Q3：报 `No module named 'docx'`

```bash
pip install python-docx
```

要出 PDF 报告的话再装：

```bash
pip install reportlab
```

### Q4：能同时装到多个 Agent 吗

**能，而且推荐。** 一个源目录可以链到任意多个位置，改一次全部生效。

如果你用的是我这台机器的同款方案，7 个目录可以一次全建：

```
~/.dsh/skills          ~/.agents/skills      ~/.claude/skills
~/.codex/skills        ~/.trae-cn/skills     ~/.zcode/skills
~/.workbuddy/skills
```

### Q5：以后怎么更新

```bash
cd ~/Documents/aigc-detox-lcw
git pull
```

如果是链接安装的，**更新完不用重装**，所有 Agent 自动用新版。

### Q6：怎么卸载

删掉那个链接就行，**不要删源目录**：

```bash
# macOS/Linux
rm ~/.agents/skills/aigc-detox-lcw

# Windows PowerShell（只删链接，不动目标内容）
[System.IO.Directory]::Delete("C:\Users\$env:USERNAME\.agents\skills\aigc-detox-lcw")
```

---

## 五、装好之后，怎么用

**你不需要记命令。** 装好之后直接跟 Agent 说人话就行：

| 你想干的事 | 你就说 |
|:--|:--|
| 先看看论文 AI 味重不重 | 「帮我看下这篇论文 AI 味重不重」+ 拖入 docx |
| 直接降 | 「这篇论文 AI 味太重了，帮我降一降」+ 拖入 docx |
| 只要报告不改稿 | 「只出报告，先别改」 |
| 改完想核对 | 「把改前改后的差异对比给我看」 |

Agent 会自动走：**体检 → 出报告 → 停下来问你 → 改写 → 复检 → 交付**。

> ⚠️ 默认流程是**出完报告就停**，等你点头才动笔。如果你确定要它直接改，就说「直接改」。

详细用法（脚本参数、每一层诊断在做什么）见 [README.md](README.md) 和 [SKILL.md](SKILL.md)。

---

## 六、最后：请务必读一遍免责声明

装完第一件事，让 Agent 把 [DISCLAIMER.md](DISCLAIMER.md) 念给你听。

核心就四句：

1. **禁止商用**，仅供个人学习研究自用。
2. **不保证通过**知网 / 格子达 / 维普 / Turnitin 等任何查重或 AI 检测系统。
3. **不要完全依赖输出**，改写结果必须你自己逐句复核，数字引用结论你自己负责。
4. **完全免费**，如果你是花钱买的，你被骗了。

**论文是你自己的学术成果。工具只是笔，署名和责任都在你身上。**
