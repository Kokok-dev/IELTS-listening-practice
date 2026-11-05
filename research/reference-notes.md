# 参考与取舍（2026-11-05）

- DailyDictation 官网公开介绍了 Listen、Write、Check & correct、Read out loud 四步。初版采用其中「先隐藏原文 → 听写 → 用户主动核对」的顺序，同时加入逐句自动停止、重播快捷键、词级差异和收藏笔记。来源：https://dailydictation.com/
- EngExam 公开目录列出了 Practice Test 1–31；没有足够明确的册号映射证明它能覆盖全部剑桥听力，直接音频页访问在本机也出现 SSL 错误。没有把这些编号当作剑桥册号。来源：https://engexam.info/ielts-listening-practice-tests/
- Engnovate 的 Cambridge Academic 分类分 7 页，实际页面包含剑桥 1–21 的 84 个测试。逐页解析 audio 标签和来源页实际出现的链接，得到 336 个 Section；没有根据猜测批量拼接音频 URL。全部执行了 HEAD 检查，保留来源、备用 URL、时间与大小。来源：https://engnovate.com/ielts-listening-tests/?category_type=cambridge-academic
- 参考软件行为和公开页面，不复制站点播放器代码。曾按用户建议调用 REA 的 `capture_browser_scenario`，客户端返回 `MCP tool call requires approval, but approval policy is never`，没有成功获得运行证据。该失败不支持任何逆向结论，因此后续参考基于可读取的公开页面。
- 模型只从魔搭固定版本下载，首次逐文件 SHA-256 校验。Faster Whisper 支持 int8 CPU、本地目录与词级时间戳；本机选 Small.en 兼顾英文识别与速度。来源：https://github.com/SYSTRAN/faster-whisper 、https://modelscope.cn/models/pengzhendong/faster-whisper-small.en
- 没有接入任何收费或有时效试用额度的云端服务；本地识别需用户核实，支持手动校正。

下载与 HEAD 检查通过 Python 显式禁用 HTTP 代理的 HTTPS 连接完成；没有改变系统网络、VPN 或证书验证设置。因此只能证明本机当时可达，不能断言所有网络环境均可访问。
