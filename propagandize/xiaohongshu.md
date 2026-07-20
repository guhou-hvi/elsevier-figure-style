# 小红书发布包：elsevier-figure-style

> 使用说明：从“标题候选”中选择一个标题，正文可直接发布。九宫格脚本用于制作配图，不需要和正文一起粘贴到平台。文末“维护备注”仅供项目维护者查看。

## 标题候选

1. **投稿前才发现论文图全要重做？我把格式规范写成了一个 Skill（推荐）**
2. **受够了每张图都重调字体、线宽和 DPI，我开源了这套论文绘图 Skill**
3. **论文图不是画完就结束：最容易被忽略的投稿返工，我做成了自动检查**
4. **明明查过期刊图片规范，为什么投稿前还是会漏？**
5. **研究生画论文图的重复劳动，终于可以少做一点了**

## 封面文案

**主标题**

投稿前才发现
论文图全要重做？

**副标题**

把容易忘、反复调的图片规范，变成贯穿写作过程的持续检查

**角标**

开源 · Elsevier-style · AI Agent Skill

## 可直接发布正文

论文都快投了，才发现图还得重做，真的很崩溃。

字体太小、图幅不对、DPI 不够、图例挡住数据、公式还是普通文本……单看每一项都不算大问题，但几张图来自不同脚本、不同软件或不同合作者时，它们会在投稿前一起找上门。

更麻烦的是：很多时候不是我们不知道图片规范重要，而是规范散落在出版社说明、目标期刊指南和编辑意见里；写论文又要持续几个月，查过的要求很容易忘。每新画一张图，还要再设置一遍尺寸、字体、线宽、marker、图例和导出参数。

所以我把自己遇到的这些问题整理成了一个开源 Skill：

**elsevier-figure-style**

它想做的不是“最后一天替你救火”，而是把检查提前到整个论文流程里：

📈 **画定量结果图时**
给线图、柱状图、热图、散点图、Pareto/frontier 和 ablation curve 套用同一套 profile，减少每张图重复写格式参数。

🔍 **写作和修改期间**
检查 Python 绘图代码有没有绕开规范，同时检查导出位图的尺寸、DPI、颜色模式、透明通道等 metadata。

👀 **投稿前**
让 Agent 实际查看最终导出效果，继续检查字号、遮挡、越界、拥挤和排版问题，而不是只看代码里“好像设置对了”。

🧩 **示意图和图形摘要**
目前可以检查可读性、重叠、对齐、panel label 和导出 metadata。v0.1 只负责审查，不会自动重绘。

Python/matplotlib 是目前支持最完整的路径；R/ggplot2 提供基础 theme 和导出支持。

安装 Skill：

```bash
npx skills add guhou-hvi/elsevier-figure-style
```

GitHub 搜索：

```text
guhou-hvi/elsevier-figure-style
```

项目使用 MIT License，也已经有 Zenodo DOI。它是一个非官方的 Elsevier-style 工具，不会承诺“一键合规”或“保证过审”；真正投稿时，目标期刊最新的 Guide for Authors 仍然是最终依据。

如果你也受够了每张图都重新调一遍格式，可以试试看。

觉得有用的话，欢迎顺手点个 Star ⭐

遇到问题或有改进建议，可以直接提 issue。也欢迎贡献你收到过的图片格式返修意见，但请只提交**获授权、已经脱敏的转述**，不要公开原始审稿通信、稿件信息或未发表结果。我希望把这些真实反馈逐渐沉淀成更完整、可复用的检查规则。

## 话题标签

#科研绘图 #论文写作 #SCI投稿 #研究生科研 #学术论文 #论文配图 #科研工具 #开源项目 #AI科研 #AIAgent #matplotlib #Elsevier #科研效率 #投稿避坑

## 九宫格脚本

### 第 1 页：封面

**主标题**

投稿前才发现
论文图全要重做？

**辅助文案**

我把容易忘、反复调的图片规范，写成了一个开源 Skill

**建议画面**

- 使用干净的浅色背景。
- 中间放一张“修改前 / 修改后”局部对比。
- 底部保留项目名 `elsevier-figure-style`。

**排版重点**

- 使用 3:4 竖版画布。
- “全要重做”作为最大字号视觉锚点。
- 不堆叠安装命令、GitHub 地址等次要信息。

### 第 2 页：规范分散

**主标题**

不是不知道规范重要
而是不知道去哪找全

**辅助文案**

字号、图幅、DPI、文件格式、颜色模式、图形摘要要求……分散在出版社说明、期刊指南和编辑意见里。

**建议画面**

- 用简洁列表表现规则来源。
- 右下角加入“写作几个月后还容易忘”的短注释。

**排版重点**

- 不展示虚构的期刊强制规则。
- 强调“规则分散”和“难以持续执行”，而不是制造投稿焦虑。

### 第 3 页：重复设置

**主标题**

每画一张图
都要重新规定一次格式？

**辅助文案**

尺寸、字体、线宽、marker、图例、DPI、保存格式……复制旧脚本，还可能把过时参数一起复制过来。

**建议画面**

- 左侧放重复出现的参数关键词。
- 右侧用箭头汇总到“共享 profile”。

**排版重点**

- 让“重复设置 → 统一 profile”的关系一眼可见。
- 避免大段代码截图。

### 第 4 页：线图 Before/After

**主标题**

同一组数据
格式真的会影响可读性

**辅助文案**

最终尺寸下检查字号、公式、线型、marker、图例与视觉层级。

**现有素材**

- `docs/assets/comparison/before-line.png`
- `docs/assets/comparison/after-line.png`

**排版重点**

- 上下或左右等宽放置 Before/After。
- 不裁掉坐标轴标题和图例。
- 标明两张图使用相同数据和坐标范围。

### 第 5 页：柱状图 Before/After

**主标题**

不只是换个配色
还要统一柱形与图例

**辅助文案**

检查柱宽、边缘、文字、刻度和图例是否在最终版面中清晰、稳定。

**现有素材**

- `docs/assets/comparison/before-bar.png`
- `docs/assets/comparison/after-bar.png`

**排版重点**

- 保留四个模型、两个阶段的完整结构。
- 不通过故意降低 Before 配色区分度制造反差。

### 第 6 页：散点图 Before/After

**主标题**

图例没有越界
也可能正在干扰数据

**辅助文案**

Agent 查看最终导出图，继续确认 marker、标签、空白区和图例是否相互遮挡。

**现有素材**

- `docs/assets/comparison/before-scatter.png`
- `docs/assets/comparison/after-scatter.png`

**排版重点**

- 保持 Before/After 相同的数据点和坐标范围。
- 放大展示图例与散点之间的安全距离。

### 第 7 页：三层检查

**主标题**

一张论文图
至少要过三层检查

**辅助文案**

1. 绘图代码：是否真正接入统一 profile。
2. 导出 metadata：尺寸、DPI、颜色模式、透明通道等是否合理。
3. 最终视觉效果：是否清晰、遮挡、越界或拥挤。

**建议画面**

- 使用纵向三段流程，不使用复杂流程图。
- 每层只保留一个图标和一句解释。

**排版重点**

- 明确 metadata checker 面向位图。
- PDF、SVG、EPS 使用人工视觉审查路线。

### 第 8 页：怎么使用

**主标题**

把 Skill 装进 Agent
直接从论文任务开始用

**安装命令**

```bash
npx skills add guhou-hvi/elsevier-figure-style
```

**示例 Prompt**

```text
使用 $elsevier-figure-style 按 editor 档生成这张论文线图，并检查导出的 TIFF。
```

**排版重点**

- 命令和 Prompt 分成两个区域。
- 注明 skills CLI 负责安装 Skill；Python/R 依赖按 README 配置。
- 不宣称当前已经可以在 skills.sh 站内搜索到。

### 第 9 页：开源共创

**主标题**

真实的返修意见
不该只修在一张图里

**辅助文案**

MIT 开源 · Zenodo DOI · 欢迎 Star、issue 和改进建议

欢迎贡献获授权、脱敏后的图片格式返修意见，让它们变成下一次可以自动检查的规则。

**建议画面**

- 显示项目名和 GitHub 仓库名。
- 使用 Star、issue、规则清单三个简单视觉元素。

**排版重点**

- 强调不得公开原始私密审稿通信。
- 结尾保留明确行动入口，不再重复罗列全部功能。

## 发布前检查

- [ ] 标题没有承诺“保证过审”或“一键合规”。
- [ ] GitHub 仓库名为 `guhou-hvi/elsevier-figure-style`。
- [ ] 安装命令可从公开 GitHub 仓库发现 `elsevier-figure-style`。
- [ ] Before/After 使用相同数据和坐标范围。
- [ ] 示意图能力表述为“审查”，没有写成“自动重绘”。
- [ ] Python 与 R 的支持边界表述准确。
- [ ] 共创邀请明确要求授权和脱敏。
- [ ] 图片中没有稿件内容、私人路径或未公开结果。

## 维护备注：skills.sh 状态（不要发布到小红书）

- 2026-07-20 已验证以下命令可以从公开 GitHub 仓库发现 Skill：

  ```bash
  npx skills add guhou-hvi/elsevier-figure-style --list
  ```

- 2026-07-20 已在临时目录完成一次 telemetry 开启的真实安装；Skill 文件和 `check_environment.py` 均验证通过，临时目录已清理。
- skills.sh 官方采用匿名安装 telemetry 自动登记，没有单独的人工提交表单。
- 真实安装后的 10 分钟观察窗内，详情页仍显示尚未收录，因此当前正文只宣传 GitHub 安装方式：

  ```text
  https://www.skills.sh/guhou-hvi/elsevier-figure-style/elsevier-figure-style
  ```

- 详情页真正生效后，再执行两项修改：
  1. 将正文中的安装说明补充为“已收录 skills.sh”，并加入详情页地址。
  2. 在中英文 README 顶部加入官方 badge：

     ```markdown
     [![skills.sh](https://skills.sh/b/guhou-hvi/elsevier-figure-style)](https://www.skills.sh/guhou-hvi/elsevier-figure-style)
     ```
