# REA 研究结果与句听 0.2 的实现

2026-11-05。研究采用 REA 启动独立临时 Chrome，在公开页面执行声明的点击和等待，保留前后页面结构。没有登录或上传用户音频，没有复制网站播放器代码。

| 来源 | 实际观察 | 句听采用的实现 |
|---|---|---|
| [DailyDictation 剑桥练习](https://dailydictation.com/exercises/ielts-listening/cam19-test-1-part-1.1383/listen-and-type) | 点击 Check 后显示 Incorrect，但只显示首个提示词，后面的答案仍被遮罩；设置面板显示自动重播次数与重播间隔 | 检查输入与展开原文分开；逐词提示；循环次数和停顿可调 |
| [Listenise 公开练习](https://listenise.com/practice?demo=1) | 点击 Cloze 后实际显示隐藏比例 30% 与滑块；切换 Shadowing 后该控件消失；切换本地文件来源显示媒体和字幕配对的就绪状态 | 同一音频切换听写 / 填空 / 听读跟读；填空比例可调；各模式独立保存答案；缺少原文时说明原因 |
| [Speechling 英式英语听写](https://speechling.com/dictation/englishb) | Give Up 才显示完整答案；Mark for Review 后显示稍后重练提示；Next 后重新隐藏答案 | 显式显示 / 隐藏原文；错误或提示过的句子加入待复习；目录可筛选待复习、未完成或收藏 |

证据索引：

- DailyDictation：`ev_3d50c00321eb9786cf0b66f2a808733d72ca116a8f267049004bd541e6a7c921`，完整文件 `rea-dailydictation-interactions.json`。
- Listenise：`ev_cc379d8da79a9669c5dd55bbfd7bb643e91bfbfd4d46666484516b21719c035e`，完整文件 `rea-listenise-modes.json`。
- Speechling：`ev_9e8c5a5e144c7739c8b94ee01706909aa458a2a593d64ab5ab3f849ea410f54a`，完整文件 `rea-other-speechling-review-next.json`。

额外实现：基于我们自己的本地 Whisper 词级时间戳，让已显示的参考词可点击重听，在听读模式随播放高亮。重新打开不会提前显示参考答案，听写、填空、播放次数、提示次数及复习标记均保存到本地。

边界：Listenise 此轮实测了练习准备区，没有进入其播放课堂；未确认其隐藏课堂控件的运行行为。Speechling 观察到“5–10 句后重现”的提示，未连续完成这些句子验证调度；句听本版实现手动待复习队列，不声称复刻该自动调度。跟读使用本地音频和文本，不使用浏览器在线语音评分。
