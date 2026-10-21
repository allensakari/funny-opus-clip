---
name: funny-opus-clip
description: 数据短视频全流程：给一个选题，问 4 个问题（风格 / 旁白 / 画幅 / 配乐），然后按「一手来源 → 脚本 → 程序动画 → 卡点配乐 → QC → 成片 → 四尺寸封面 → 各平台发布稿」做出全部发布素材。默认不配音（纯音乐 + 字幕）、9:16 约 90 秒、四尺寸封面。频道的名字、标志、颜色、字体都在 profiles/<频道>/profile.toml。Use when the user says /funny-opus-clip, gives a topic for a short data / science clip, says 做一期 / 数据短视频 / data clip, or asks for 封面 / 发布稿 for an episode made with this skill.
---

# funny-opus-clip · 数据短视频

用户只需要给**一个选题**。第 0 步问 4 个问题，答案写进 `episode.toml`，之后每一步都按它做，不再重复问。

| 项 | 内容 |
|---|---|
| 根目录 `$ROOT` | 本 skill 的目录（即 GitHub 仓库 allensakari/opus-funny-clip 的克隆）：`engine/`、`skill/styles/`、`profiles/`、`assets/`；每期的工程放 `$ROOT/episodes/`（不入库） |
| Python | `$ROOT/.venv/bin/python`（`uv sync`）；需要 ffmpeg |
| 频道配置 | `profiles/<频道>/profile.toml`；用哪个由 `profiles/DEFAULT`（一行，默认 `example`）或 `STORY_PROFILE=<目录>` 决定。频道名、标志、配色、字体、合集、关注语（以及可选的 TTS）都在这里，**流程和引擎里不写死任何频道的东西** |
| 密钥 | 只有用户主动要配音（或用 Lyria 配乐）时才需要，放 profile 的 `tts.env_file` 指向的 `.env`（不入库，模板 `.env.example`）。**只让用户自己编辑这个文件，不在对话里收密钥，不打印值**；`episode.py check` 只报变量名 |
| 本期答案 | 期目录的 `episode.toml`（`engine/episode.py` 写入和读取） |
| 风格 | `skill/styles/index.toml`（能力表）+ `skill/styles/<风格>/STYLE.md`（做法，覆盖本文件的对应项） |
| 曲库 | `assets/music/music.toml`（每首的授权和署名原文；音频文件本身不入库） |

## 一、流程总览

| 步 | 做什么 | 产出 | 停 |
|---|---|---|---|
| 0 | 开工问答 | `episodes/<编号_片名>/episode.toml` | ⏸ 4 个问题（一次问完） |
| 1 | 研究 | `data/`、`stats.py`、`来源表.md` | ⏸ 节点 ①：来源表 + 2–3 个钩子角度 |
| 2 | 脚本 | `script.py` / `timeline.py` + `脚本.md` | ⏸ 节点 ②：脚本 + 两种结尾 |
| 3 | 配音（默认不配音，跳过） | `build/voice/` | |
| 4 | 时间轴 + 配乐 | 时间轴、配乐 | |
| 5 | 画面 + 混音 + QC | `build/video*.mp4`、`qc.txt`、`transqc.txt` | ⏸ 节点 ③：QC 0 个问题 + 样帧 + 草稿 |
| 6 | 成片（`formats` 里的每个画幅） | `发布/<片名>[_横版].mp4` + `.srt` | |
| 7 | 封面（四个尺寸，不问） | `发布/封面_9x16 / 3x4 / 16x9 / 4x3.jpg` | |
| 8 | 发布稿 + 吸粉 | `发布/发布稿.md`、`CREDITS.md`、`来源表.md`、`壁纸/` | ⏸ 节点 ④：全部素材 |

节点 ①–④ 必须停下等用户确认。用户只说「全自动」「不用停」时，节点 ①–③ 改成只汇报不等待，节点 ④ 照停。用户在任何节点改了方向，回到对应的步骤重做，再从那个节点往下走。

## 二、逐步做法

### 0. 开工问答

1. **选题**：用户给了就用。没给就推荐 5 个，每个附核心数字、钩子、可能的一手来源，让用户挑。
2. **环境自检**：`python engine/episode.py check`（还没有期目录时在任意空目录跑）。字体、标志、ffmpeg 缺了先补。用户第一次用、还在用 `example` 频道时，提一句可以换成自己的频道：复制 `profiles/example/` 为 `profiles/<名字>/`，改 `[channel]` 的名字，`python engine/make_marks.py` 生成标志，`profiles/DEFAULT` 改成 `<名字>`；用户不想改就继续用 example。
3. **用一次 AskUserQuestion 问 4 个问题**（选项按 `skill/styles/index.toml` 生成）：

| # | 问题 | 选项 |
|---|---|---|
| 1 | 用哪种风格？ | 从能力表里挑最适合本选题的 4 个，最合适的放第一个并标「(Recommended)」；描述 = `pitch` + 「适合：`fits`」+ 原生画幅；`voice = "required"` 的风格（数据讲述）写明「必须配音」。其余风格在问题里点名，用户可以从「Other」选 |
| 2 | 要不要旁白配音？ | 「不配音（纯音乐 + 字幕）(Recommended)」/「要配音」。**默认不配音；描述里不提 TTS、密钥或接入步骤** |
| 3 | 要不要 16:9 横版？ | 「只出 9:16（约 90 秒）(Recommended)」/「9:16 + 16:9 横版」 |
| 4 | 配乐用什么？ | 「程序合成（原创，没有版权问题）(Recommended)」/「免版权曲库（要署名，见 music.toml）」 |

封面不问：四个尺寸都做。

4. **写入并核对**：

```bash
mkdir -p episodes/<编号_片名> && cd episodes/<编号_片名>
python ../../engine/episode.py init --topic "<选题>" --style <风格键> --voice no|yes --land no|yes --music synth|library
```

- `init` 会按风格能力改掉做不到的组合并打印「注意」（例如纯音乐风格不能配音、横版原生风格没有 9:16）。**如果被改掉的正是用户刚选的东西，要告诉用户，问一次：换风格，还是接受调整。**
- 最后的自检有 ✗ 就先处理：
  - **只在用户选了「要配音」时**才检查 TTS。没配好时先用不需要密钥的 `edge`（`TTS_PROVIDER=edge`，音色 `zh-CN-YunxiNeural`），不让用户去申请密钥；用户自己说要换 Gemini / OpenAI，才告诉他在 `.env` 里加哪个变量（只给变量名）。
  - **曲库是空的**：按 `music.toml` 的 `url` 下载，或改用程序合成。
- 全部 ✓ 后汇报本期设定（风格 / 旁白 / 画幅 / 时长 / 配乐 / 封面 / 平台），直接进第 1 步。

### 1. 研究 → ⏸ 节点 ①

- 原始数据或报告下载到 `data/`、`sources_raw/`。写 `stats.py`（可复现，结果写进 `data/stats_out.txt`）和 `来源表.md`（数字 | 口径 | 一手来源链接 | 定位 / 原文）。
- **只用一手来源**：官方统计、同行评议论文、机构原始数据库或年报。新闻、百科只用来顺藤摸瓜。每个数字记链接 + 页码 / 表号 / 字段 + 数据日期。
- 自己算出的数字，参数和结果都写进 `stats.py`，画面标「计算」或「模拟：参数……」。
- **人的尺度**：开头大数字之后紧接一个人能感受到的换算（每天 / 每秒、一个红灯、一节车厢），也由一手数字直接算出。
- 论文是 CC BY-NC-ND 时只引用数字，图按数据自己重画。
- 节点 ① 给：来源表 + 2–3 个钩子角度（附推荐理由）。

### 2. 脚本 → ⏸ 节点 ②

- 配音：`script.py`（`(屏幕显示, 读法)`，`[..]` 为强调色，格式见 `engine/scriptlib.py`）；不配音：字幕写进风格的时间轴（`CAPS`）。都另写一份 `脚本.md`（段 / 时间 / 旁白或字幕 / 画面 / 问题 / 答案 / 来源编号）。
- **讲述线**：「现象 → 为什么 → 怎么算 / 怎么验证 → 反转或回到你」，每一章回答上一章末尾留下的问题。旁证例子只在能推进逻辑时才放。
- **节奏**：0–3 s 第一句说出封面上的大数字（第一帧就显示），再转到更尖锐的角度；约每 8–12 s 一次转折；结尾回扣开头。
- **悬念链**：观众在「答案刚揭晓」处走得最多。
  - 每段按「问题 → 过程 → 答案」排，答案是这一段的最后一句，后面不再补论证。
  - 答案之后，下一段第一句是 ≤ 10 字的问句或转折。
  - `脚本.md` 加「问题 / 答案」两列自检。
- **措辞要准**：不用「指数级」「必然」「100%」这类数学上不成立的说法。语气平实，不写成悬疑腔。
- **字幕长度**（不配音时）：每秒不超过约 6 个汉字。
- **结尾写两种**让用户选：闭环版（最后一句 = 开头钩子，可无缝重播）/ 提问版（问观众身边某个具体的人或时刻，别把受众限定得太窄）。
- 时长按 `episode.toml` 的 `duration`（9:16 默认约 90 s）；明显超出时在节点 ② 说明理由。

### 3. 配音（只在 `voice = true` 时；默认跳过）

- `python ../../engine/voice.py [段名 …]` → `build/voice/<段>.wav` + 逐字对齐 + `check.txt`。
- 音色：`VOICE=<键>`（`takes.env`）> `episode.toml` 的 `tts_voice` > profile 的 `tts.default_voice`。服务商由音色的 `provider` 或 `tts.provider` 决定（`engine/tts.py`：gemini / openai / edge）。
- 风格提示 = profile 的 `tts.style`，每段可在 `script.py` 的 `STYLES` 里覆盖；`tts.pronunciation` 自动拼在后面；`tts.tempo` 保持音高变速。
- 数字在「读法」里写成汉字。多音字、易错声调在 `STYLES[段名]` 里写明拼音，出 2–3 个 take 让用户听。
- **自检**：读 `check.txt`。同音字差异通常是 Whisper 的偏差；错字、尾音被听歪就 `GM_TAKES="段=2"` 重合成，直到读对。选定的 take 写进 `takes.env`。

### 4. 时间轴与配乐

- 配音：`engine/timeline.build(SEGMENTS, 'build/voice', beat, unit=2)`；切点落在半小节（需要精确卡点时落到 8 分音符）。不配音：按风格 STYLE.md，镜头卡在配乐的拍点上。
- **`music = "synth"`**：用风格自带的合成工具写本期配乐（数据讲述参考 `example` 期的 `audio.py`；印刷卡通 / 等距微缩用 `print_cartoon_audio.py`；其余见 STYLE.md）。先定 BPM 和段落情绪，再按段落写配器，情绪高点对准高潮段。
- **`music = "library"`**：从 `music.toml` 按情绪和 BPM 选 2–3 首，`engine/beats.py <曲子>` 测拍，挑最贴的；把选中曲子写进 `episode.toml` 的 `music_track`，它的 `credit` 原文进 CREDITS 和发布稿。
- 换曲比较时输出带后缀，**不覆盖**已有版本，落选版本归档到 `build/review/versions/`。

### 5. 画面 + 混音 + QC → ⏸ 节点 ③

**画面**：按风格的 STYLE.md 和工具包。数据讲述用 `render.py`（每段一个场景函数，数字用 `bignum(src=...)` / `source_tag()`，最后 `captions.draw(...)` 和 `watermark(...)`）。

- `--still t` 出样帧自查：字幕区不被挡；平台界面遮挡区（右侧 x>920、y 900–1620，底部 y>1540）不放关键信息；片尾标志出现前场景文字已淡出。
- 任何镜头不超过约 3 秒只有字幕在变。
- 画面上的累计数字跟着画面上的年份 / 进度走，不只保证终点正确。
- `formats` 含 `16x9` 时，横版单独排版（`FILM_W=1920 FILM_H=1080` 或风格的 `VERT` / `LAND` 开关），不是把竖版裁一下。

**混音**：人声约 −16 dB，配乐自动压低；界面音效（`engine/uisfx.py`：落定、滑入、计数、生长、转场）对准画面事件，压在人声下。

**自动 QC（必须 0 个问题）**：
- `python ../../engine/qc.py`（横版加 `--land`）：文字互相重叠、压在关键图形上、进入平台安全区、片尾仍有场景文字、出画。
- `python ../../engine/transqc.py build/video.mp4`：单帧闪烁、淡出中亮度回升。有意的闪光用 `--ignore` 跳过，并在节点 ③ 逐条说明。

**节点 ③ 给**：读音报告（配音时）+ 两份 QC + 样帧拼图 + 草混 / 草稿视频（`build/review/`）。

### 6. 成片

- `formats` 里的每个画幅都再跑一次 QC 和转场 QC，都要 0 个问题。
- `python ../../engine/finalize.py build/video.mp4 build/mix.wav 发布/<片名>.mp4`：−14 LUFS、细颗粒防色带、H.264 12 Mbps，同时出 `.srt`。
- ffprobe 核对：竖版 1080×1920，横版 1920×1080。

### 7. 封面（四个尺寸都做，不问）

- 母版 4 种（`engine/covers.make`）：巨数字 / 对比 / 实景+数字 / 图表，按选题选一种并说明理由。
- **9:16、3:4、16:9、4:3 全部出**（`发布/封面_*.jpg`）；平台列表里有 YouTube 且有横版时，另出英文 `封面_YouTube_16x9.jpg`。
- 底图用本期引擎原生渲染（不带文字层），竖版和横版各渲染一张，`zoom` / `shift` 按尺寸调主体位置。给 2–4 张底图并排比较。
- 只放一个大数字 + 一句钩子，不放片名。参数写进期目录的 `make_covers.py`。

### 8. 发布稿 + 吸粉 → ⏸ 节点 ④

按 profile 的 `channel.platforms` 逐个平台写进 `发布/发布稿.md`：

- **标题短**（小红书 ≤ 20 字）。正文一行「数据：机构 A、机构 B 等一手来源｜完整出处见置顶评论」。
- **置顶评论两版**：精简版 ≤ 150 字，按编号「数字 → 机构 + 年份」，最后一句指向完整出处；完整版列报告名、页码和日期。
- 话题标签：发布前查各平台当期活动，相关的加进去。profile 有 `credits_line` 时加在正文末尾。
- 不写「转发给 TA」「关注才给」「私信领取」这类诱导分享 / 关注的话。
- **YouTube**（只发横版）：标题、说明、置顶评论都用 ```text 代码块；正文不写 `<` `>`；标签逗号分隔、标签内不能有空格（多词写成驼峰）。
- `CREDITS.md`：数据来源、画面（程序生成，不用 AI 生成图像）、配乐（合成：「原创合成」；曲库：`music.toml` 的 `credit` 原文）、字体授权。
- **吸粉**：
  - 从 profile 的 `channel.collections` 选一个合集。
  - 3 张手机壁纸（1290×2796，本期引擎原生渲染）放 `发布/壁纸/`。
  - 正文最后一句是互动问题，加上 profile 的 `follow_line`。

**节点 ④ 给**：成片（每个画幅）+ 四尺寸封面 + 发布稿 + CREDITS + 来源表 + 壁纸。用户确认后归档本期，更新根目录 README 的期数表。

## 三、全片通用规则（风格 STYLE.md 可覆盖）

| 项 | 规则 |
|---|---|
| 规格 | 1080p、30 fps（风格另有规定按风格）、H.264；竖版 1080×1920，横版 1920×1080 |
| 颜色编码 | 有「两方」的选题全片锁定一对颜色（profile `colors.pair`），含义从头到尾不变；品牌强调色只做强调 |
| 色温叙事 | 铺垫段偏冷，转折 / 结论段回暖（`engine/grade.py`） |
| 转场 | 优先共享元素变形（`engine/morph.py`）；硬切只留给大场景跳转 |
| 主题 | 太空 / 夜晚用 `dark`，生命 / 自然 / 社会用 `sand`（`SHUSHUO_THEME=sand`）；品牌点、标志、字体不变 |
| 画面标注 | 每个关键数字下方标「机构 · 年份」 |
| 素材 | 程序动画 + 明确可商用的公版素材（NASA、Wikimedia PD / CC BY 等）；**不用 AI 生成图像** |
| 版本 | 不覆盖旧版本；每次改动出带后缀的新文件，旧版归档到 `build/review/versions/` |
