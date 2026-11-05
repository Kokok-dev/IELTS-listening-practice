# 第三方组件与参考来源

本软件为个人精听练习工具。剑桥音频不随完整目录批量打包，目录保留公开来源链接，使用时由用户选择下载。剑桥 IELTS 音频与考试名称的权利归相应权利人，软件不声称对其拥有版权。

- 音频目录来源：<https://engnovate.com/ielts-listening-tests/?category_type=cambridge-academic>
- 精听流程参考：DailyDictation 的 Listen → Write → Check & correct → Read out loud：<https://dailydictation.com/>
- 0.2 练习模式参考：Listenise 的 Dictation / Cloze / Shadowing 公开准备界面：<https://listenise.com/practice?demo=1>。
- 0.2 难句复习流程参考：Speechling 英式英语听写：<https://speechling.com/dictation/englishb>。研究执行记录与证据 ID 保存在源码的 research 目录中。
- 切句、听写、保存与界面为本项目自行实现，没有复制参考网站的播放器代码。
- Faster Whisper（MIT）：<https://github.com/SYSTRAN/faster-whisper>
- Whisper 英语识别模型：<https://github.com/openai/whisper>；本地 CT2 文件来自 <https://modelscope.cn/models/pengzhendong/faster-whisper-small.en>，固定提交 `c7a761afd35db1cffceab396a381b326093b9b2a`。
- CTranslate2（MIT）：<https://github.com/OpenNMT/CTranslate2>
- Silero VAD（MIT，Faster Whisper 随附）：<https://github.com/snakers4/silero-vad>
- FastAPI（MIT）：<https://github.com/fastapi/fastapi>
- Uvicorn（BSD-3-Clause）：<https://github.com/encode/uvicorn>
- pywebview（BSD-3-Clause）：<https://github.com/r0x0r/pywebview>
- pythonnet（MIT）：<https://github.com/pythonnet/pythonnet>
- NumPy（BSD-3-Clause）：<https://numpy.org/>
- PyAV（BSD-3-Clause，及其随附 FFmpeg 库许可）：<https://pyav.org/docs/stable/>
- ONNX Runtime（MIT）：<https://github.com/microsoft/onnxruntime>
- Tokenizers（Apache-2.0）：<https://github.com/huggingface/tokenizers>
- PyInstaller（GPL-2.0-or-later 带运行时分发例外）：<https://pyinstaller.org/en/stable/license.html>

打包时保留各 Python 分发包的原始 license / dist-info 元数据。以上列出主要直接组件，完整依赖版本见源码中的 requirements.txt 与构建环境。
