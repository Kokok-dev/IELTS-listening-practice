"""Pinned domestic model download; local CPU inference only."""
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import urllib.parse
import urllib.request

REPO = 'pengzhendong/faster-whisper-small.en'
REVISION = 'c7a761afd35db1cffceab396a381b326093b9b2a'
FILES = {
    'config.json': (2657, '666a9605530ac1f61fa8177f3702b4dacec9966749e42610839fcc32661d5fae'),
    'model.bin': (483545366, '62b2a45b05ee59acb4a5341b33ee35e041395d378d418a18acfe4c9e768ee37a'),
    'tokenizer.json': (2128466, '929c5252409436dce1b38a75d1abbcb5e132d170d8e324e4e04ed915fa2d22df'),
    'vocabulary.txt': (422309, 'ff77588746d3a2595d32ab5b69ffd7b95ce2441ac57533cb66fc3eb575a115cf'),
}


def direct_opener():
    # No dependency on an HTTP proxy / VPN. HTTPS certificate verification stays on.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Recognizer:
    def __init__(self, path: Path):
        self.path = path
        self.model = None
        self.lock = threading.Lock()

    def ready(self):
        return all((self.path / name).exists() and (self.path / name).stat().st_size == size
                   for name, (size, _) in FILES.items()) and (self.path / 'verified.json').exists()

    def download(self, report):
        with self.lock:
            self.path.mkdir(parents=True, exist_ok=True)
            total = sum(v[0] for v in FILES.values())
            completed = 0
            opener = direct_opener()
            for name, (size, expected) in FILES.items():
                path = self.path / name
                if path.exists() and path.stat().st_size == size:
                    if hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() == expected:
                        completed += size
                        continue
                url = 'https://modelscope.cn/api/v1/models/' + REPO + '/repo?Revision=' + REVISION + '&FilePath=' + urllib.parse.quote(name)
                tmp = path.with_suffix(path.suffix + '.part')
                for attempt in range(3):
                    try:
                        digest = hashlib.sha256()
                        received = 0
                        with opener.open(url, timeout=40) as response, tmp.open('wb') as out:
                            while chunk := response.read(1024 * 1024):
                                out.write(chunk)
                                digest.update(chunk)
                                received += len(chunk)
                                report(min(98, (completed + received) / total * 100), f'正在从魔搭下载英语模型 · {(completed + received)/1e6:.0f} / {total/1e6:.0f} MB')
                        if received != size or digest.hexdigest() != expected:
                            raise ValueError('模型文件校验失败，请重试。')
                        os.replace(tmp, path)
                        break
                    except Exception:
                        if attempt == 2:
                            raise
                        time.sleep(1)
                completed += size
            (self.path / 'verified.json').write_text(json.dumps(dict(repo=REPO, revision=REVISION, files=FILES)), 'utf-8')

    def transcribe(self, audio: Path, report):
        if not self.ready():
            raise ValueError('请先在设置中下载本地英语识别模型（约 486 MB）。')
        with self.lock:
            if self.model is None:
                report(1, '正在加载本地英语模型…')
                from faster_whisper import WhisperModel
                self.model = WhisperModel(str(self.path), device='cpu', compute_type='int8',
                                          cpu_threads=min(8, max(2, (os.cpu_count() or 4) // 2)),
                                          local_files_only=True)
            from .audio import read_wav
            # The app has already decoded to 16kHz mono. Feeding samples avoids
            # decoding twice and PyAV API drift in faster-whisper's file helper.
            chunks, info = self.model.transcribe(read_wav(audio), language='en', beam_size=5,
                word_timestamps=True, vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500), condition_on_previous_text=False,
                hallucination_silence_threshold=2)
            words = []
            raw = []
            for chunk in chunks:
                raw.append(dict(start=chunk.start, end=chunk.end, text=chunk.text.strip()))
                for w in chunk.words or []:
                    words.append(dict(start=round(w.start,3), end=round(w.end,3), word=w.word,
                                      probability=round(w.probability,3)))
                report(min(99, chunk.end / max(info.duration,1) * 100), f'正在本地识别 · {chunk.end:.0f} / {info.duration:.0f} 秒')
            return words, raw
