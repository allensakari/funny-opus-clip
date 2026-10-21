# 频道配置（profiles/）

引擎（`engine/`）和流程（`SKILL.md`、`skill/styles/`）是通用的；只属于一个频道的东西放在 `profiles/<频道>/`：

| 文件 | 内容 |
|---|---|
| `profile.toml` | 频道名、配色（含浅色主题）、字体、标志图和点的位置、合集、关注语；可选的旁白设置（`[tts]`） |
| `marks/` | 水印和片尾标志（白色透明 PNG，不含点；点由引擎按 `colors.accent` 画）|

用哪个：`profiles/DEFAULT` 里写的名字（默认 `example`），或临时 `STORY_PROFILE=<目录>`。

## 做自己的频道

```bash
cp -r profiles/example profiles/mychannel
# 编辑 profiles/mychannel/profile.toml：[channel] name / name_en / follow_line，[colors] accent
.venv/bin/python engine/make_marks.py        # 先把 DEFAULT 改成 mychannel，或者加 STORY_PROFILE=profiles/mychannel
echo mychannel > profiles/DEFAULT
```

`make_marks.py` 按频道名生成文字标志（圆环 + 名字；片尾名字 + 句点），并把坐标写进 `[marks]`。

## 用自己的标志图

画两张白色透明 PNG，**不画那个点**（点由引擎画，颜色是 `colors.accent`），然后量出坐标填进 `[marks]`：

| 键 | 含义 |
|---|---|
| `wm_dot` | 小标志里点的位置（像素） |
| `wm_bbox` | 小标志图形的左上角（裁掉透明边） |
| `wm_letter_end` | 先从点里长出来的部分（首字母 / 图形）的右边界 |
| `wm_name_end` | 名字的右边界 |
| `logo_dot` / `logo_dot_r` | 片尾标志里句点的位置和半径 |
| `logo_center_x` | 片尾标志的水平中心 |
| `logo_name_x` | 片尾名字从句点向左展开到的位置 |

英文版（`BRAND_LANG=en`，YouTube 用）放 `[marks.en]`，坐标与中文版相同。

## 旁白（可选）

默认不配音。要配音时 `[tts]` 选服务商（`engine/tts.py`）：`edge` 不要密钥；`gemini` / `openai` 的密钥写进仓库根目录的 `.env`（见 `.env.example`，不入库）。
