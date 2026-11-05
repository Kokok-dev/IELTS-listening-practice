# 句听 · IELTS 精听 0.3

## 写在前面（只有这段是我自己写的）
只用下载installer里面的文件，其他的是源代码\
这个软件主要是帮你提升听力的，可能做的没有像dailydictation那么好，但是是完全开源的，并且听力原文都是本地识别的，除了剑雅题目需要联网下载，其他都不需要网络\
有问题可以找我 2971731417@qq.com 当然你应该清楚很多时候问我不如问chatgpt"What the hell is this shit?"（怪不好意思的，应该在旁边的distributor加一个chatgpt）

## 正文开始（以下开始就是gpt写的了，写的啥我也不太看得懂）

Windows 本地精听工具。导入音频后先提供停顿预览，识别后按模型标点与词时间戳切句。剑桥目录音频优先使用来源网站现成文本，匹配音频后逐句练习；其他音频使用本地 Whisper 原文。没有现成时间戳时，首次仍需本地模型定位，之后复用缓存。

0.3 增加播报跳过开关、关键词优先填空、重点句与抽练范围、在线音频缓存清理及恢复。重新切句前备份，迁移后的输入标为待复习；人工校正的分句保留。网页文本匹配失败会提示并回退，不保证第三方文本与所有音频版本一致。

已经包含剑桥 IELTS 1–21 的音频目录：84 套 Test、336 个 Section。只保存索引；点击时下载、切句和缓存。来源为 Engnovate 的公开音频页面，保留每份音频的来源链接和备用链接。索引更新时间为 2026-11-05。

## Windows 使用

安装版：运行 `outputs/句听-安装程序-v0.2.0.exe`，按向导选择目录并创建快捷方式。通过快捷方式启动时，学习记录保存在 `%LOCALAPPDATA%\Juting\data`；卸载保留记录。安装包不包含个人音频和示例学习记录。迁移便携版记录见 [安装说明](installer/安装说明.md)。

打开 `outputs/句听/句听.exe`。无需 Python，无需 API Key。请保留同目录的 `_internal`、`models` 和 `data` 文件夹。

完整说明见 [使用说明.md](使用说明.md)。

## 开发

需要 Windows x64 / Python 3.12、Microsoft Edge WebView2 Runtime。

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --no-cache-dir -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
.venv\Scripts\python main.py
```

浏览器调试：`.venv\Scripts\python main.py --serve --port 8876`。

测试：`.venv\Scripts\python -m pytest -q`（测试额外需要 pytest、httpx）。

打包：`.venv\Scripts\python tools/build_windows.py`。结果先放在 `outputs/staging-v0.2.0/句听`，不覆盖正在运行的程序或用户记录。关闭旧版后，可运行 `tools/prepare_release_v02.py` 备份并更新程序文件，保留现有 data 与 models。

练习逻辑检查：`node --test tests/practice-core.test.cjs`。

安装包构建：先生成暂存版，再执行 `.venv\Scripts\python tools/build_installer.py --iscc "你的 Inno Setup 6 安装目录\ISCC.exe"`。脚本在 `installer/`，成品在 `outputs/`。上传 GitHub 源码时包含 `installer/`；EXE 安装包通过 Releases 分发。

## 实现

- FastAPI 仅监听 `127.0.0.1`，随机会话 token 保护写请求，并验证 Host/Origin。
- PyAV 解码为 16kHz 单声道 WAV；20ms RMS 能量检测持续停顿，自适应安静录音阈值，对长段落选择局部低能量点切分。
- Faster Whisper Small.en 使用 CPU int8，词级时间戳映射到音频片段。模型固定至魔搭特定版本，下载后校验 SHA-256，推理不自动访问 Hugging Face。
- 句子播放用浏览器音频及 requestAnimationFrame 停止边界，后台标签页有 timeupdate 兜底。Windows 音频调度会有少量时间误差。
- JSON 原子替换持久化；前端草稿兜底；重切和手动边界调整前自动备份。
- `tools/build_catalog.py` 从公开目录提取实际音频链接；`tools/verify_catalog.py` 以 HEAD 检查音源，不批量下载完整音频。

限制：停顿分段不保证语法上的整句；参考原文可能识别错误；本版不实现雅思试题作答评分、翻译、账号同步或云端转录。导出的 JSON 是记录导出，本版尚无 JSON 恢复入口，完整迁移请复制 data 文件夹。
