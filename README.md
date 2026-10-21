# funny-opus-clip

to create funny clip with claude opus

一个 [Claude Code](https://claude.com/claude-code) skill：**给一个选题，回答 4 个问题，就按完整流程做出一期数据 / 科普短视频的全部发布素材**：成片、字幕、四个尺寸的封面、各平台发布稿、来源表、署名和手机壁纸。

A Claude Code skill that turns one topic into a finished short data / science clip: primary-source research, script, programmatic animation, beat-synced music, automatic QC, final video, covers in four sizes and per-platform post copy (Douyin, Xiaohongshu, Bilibili, YouTube). The workflow text is in Chinese.

## 开工时只问 4 个问题

| 问题 | 默认 |
|---|---|
| 1. 风格 | 按选题推荐（见下表） |
| 2. 旁白配音 | **不配音**（纯音乐 + 字幕） |
| 3. 16:9 横版 | 不做，只出 9:16 约 90 秒 |
| 4. 配乐 | 程序合成（原创，无版权问题）；或免版权曲库 |
| 封面 | 不问，9:16、3:4、16:9、4:3 全部出 |

| 风格 | 一句话 | 原生画幅 |
|---|---|---|
| 数据讲述 `data` | 配音 + 数字跳格字幕，skia / moderngl 程序动画（必须配音） | 9:16 |
| 印刷卡通 `print-cartoon` | 米色纸面、胶囊小人、120 BPM 动作卡 | 横竖两版 |
| 写实宇宙 `cosmic-real` | 光线追踪 3D 宇宙，镜头卡在情绪曲拍点上 | 16:9 |
| 光点粒子 `particle-math` | 彩虹光点一镜到底，数学对象互相变形 | 16:9 |
| 等距微缩 `iso-diorama` | 等距微缩世界，移轴虚化（新风格） | 横竖两版 |

做不到的组合（比如纯音乐风格选了配音、横版风格要 9:16）会在开工时自动调整并说明。

## 安装

需要：macOS（Apple Silicon 上测试过；moderngl 需要 OpenGL 3.3+）、[uv](https://docs.astral.sh/uv/)、ffmpeg、Claude Code。

```bash
git clone https://github.com/allensakari/funny-opus-clip.git ~/.claude/skills/funny-opus-clip
cd ~/.claude/skills/funny-opus-clip
uv sync
.venv/bin/python engine/episode.py check     # 环境自检
```

## 使用

在 Claude Code 里：

```
/funny-opus-clip 钍-229 核钟：一道找了 48 年的光
```

Claude 问完 4 个问题后按流程做，在 4 个节点停下来等你确认（来源表 / 脚本 / 样片和 QC / 全部素材）。每期的工程在 `episodes/<编号_片名>/`，发布素材在它的 `发布/` 里。

## 目录

```
SKILL.md                 流程（skill 入口）
skill/styles/            风格：index.toml（能力表）+ 每种风格的 STYLE.md、工具包、参考工程 templates/
engine/                  引擎：品牌层、字幕、封面、QC、转场 QC、成片、时间轴、音效、旁白（可选）
profiles/                频道配置：example/（示例频道）、DEFAULT（当前用哪个）
assets/fonts/            字体（全部 SIL OFL 1.1，附授权文本）
assets/music/music.toml  免版权曲库清单（Kevin MacLeod，CC BY 4.0；音频按 url 自己下载）
episodes/                你的每一期（不入库）
```

换成自己的频道名、颜色和标志：见 `profiles/README.md`（`engine/make_marks.py` 可以按频道名生成文字标志）。

## 说明

- 只用一手来源（官方统计、同行评议论文、机构数据库），每个数字在来源表里有出处；画面全部程序生成，不用 AI 生成图像。
- 旁白默认关闭。要配音时 `engine/tts.py` 支持 edge（免费、无密钥）、Gemini、OpenAI；密钥只放 `.env`（不入库）。
- 参考工程（`templates/`）只含代码：纹理、配乐、参考歌曲等媒体文件不随仓库提供。

## 授权

- 代码、skill 文本、风格说明、示例频道配置：[MIT](LICENSE)，任何人都可以自由使用、修改、商用，保留版权声明即可。
- `assets/fonts/` 里的字体是 SIL Open Font License 1.1（授权文本在同一目录），可以随片使用和再分发，但不能单独出售字体。
- `music.toml` 里的曲子（Kevin MacLeod，CC BY 4.0）不随仓库提供；用了就要按 `credit` 署名。
