"""Audio decoding and pause-based segmentation. No external FFmpeg required."""
from pathlib import Path
import uuid
import wave
import numpy as np

RATE = 16000


def decode(source: Path, target: Path) -> tuple[np.ndarray, int]:
    import av
    chunks = []
    limit = RATE * 60 * 180
    count = 0
    with av.open(str(source)) as container:
        resampler = av.AudioResampler(format='s16', layout='mono', rate=RATE)
        for frame in container.decode(audio=0):
            for item in resampler.resample(frame):
                chunk = item.to_ndarray().reshape(-1)
                count += len(chunk)
                if count > limit:
                    raise ValueError('音频最长支持 3 小时，请先按 Test 或 Section 分开导入。')
                chunks.append(chunk)
        for item in resampler.resample(None):
            chunks.append(item.to_ndarray().reshape(-1))
    if not chunks:
        raise ValueError('没有读取到音轨，请尝试 MP3、WAV、M4A 或 FLAC。')
    pcm = np.concatenate(chunks).astype('<i2')
    with wave.open(str(target), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())
    return pcm.astype(np.float32) / 32768.0, RATE


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), 'rb') as source:
        return np.frombuffer(source.readframes(source.getnframes()), dtype='<i2').astype(np.float32) / 32768.0


def new_segment(start: float, end: float, reason: str = 'pause') -> dict:
    return dict(id=uuid.uuid4().hex[:12], start=round(start, 3), end=round(end, 3),
                text='', answer='', done=False, starred=False, note='', reason=reason, text_source='')


def split_pauses(samples: np.ndarray, rate: int = RATE, pause: float = .45,
                 threshold_db: float = -36, max_length: float = 18.0) -> tuple[list[dict], list[float], float]:
    """20ms RMS frames, sustained silence, padded speech, low-energy long cuts.

    Silence-only input has no segments. Short intra-word dips never create cuts.
    Long speech runs split at the lowest-energy frame near the desired boundary.
    """
    if not (.15 <= pause <= 2 and -65 <= threshold_db <= -15 and 5 <= max_length <= 40):
        raise ValueError('切句参数超出范围。')
    hop = max(1, int(rate * .02))
    n = len(samples)
    if n == 0:
        return [], [], threshold_db
    frames = np.pad(samples, (0, (-n) % hop)).reshape(-1, hop)
    rms = np.sqrt(np.mean(frames * frames, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    # Lower the gate for quiet recordings; the requested gate remains the ceiling.
    ceiling = float(np.percentile(db, 90)) - 20
    gate = max(-65., min(threshold_db, ceiling))
    voiced = db > gate
    indices = np.flatnonzero(voiced)
    peaks = np.max(np.abs(frames), axis=1)
    stride = max(1, len(peaks) // 3600)
    waveform = [round(float(v), 3) for v in peaks[::stride]]
    if not len(indices) or float(np.max(rms)) < .00008:
        return [], waveform, gate
    groups = []
    first = last = int(indices[0])
    for i in indices[1:]:
        if (int(i) - last - 1) * .02 >= pause:
            groups.append((first, last + 1))
            first = int(i)
        last = int(i)
    groups.append((first, last + 1))
    duration = n / rate
    segments = []
    for left, right in groups:
        # Ignore isolated clicks shorter than 80ms, but retain spoken short words.
        if right - left < 4:
            continue
        start = max(0., left * .02 - min(.12, pause * .38))
        end = min(duration, right * .02 + min(.16, pause * .48))
        while end - start > max_length:
            lo = int((start + max_length * .62) / .02)
            hi = min(len(db), int((start + max_length - .15) / .02))
            if hi <= lo:
                break
            # Smooth the local energy to avoid selecting a single noisy zero-crossing.
            energy = np.convolve(rms[lo:hi], np.ones(5) / 5, mode='same')
            energy[:3] = energy[-3:] = np.inf
            cut = (lo + int(np.argmin(energy))) * .02
            segments.append(new_segment(start, cut, 'length'))
            start = cut
        if end - start >= .12:
            segments.append(new_segment(start, end))
    return segments, waveform, round(gate, 1)


def align_words(segments: list[dict], words: list[dict]) -> None:
    """Assign each word once, using its midpoint, never overwriting manual text."""
    if not segments:
        return
    buckets = [[] for _ in segments]
    for word in words:
        middle = (word['start'] + word['end']) / 2
        index = min(range(len(segments)), key=lambda i: max(segments[i]['start'] - middle, middle - segments[i]['end'], 0))
        buckets[index].append(word['word'])
    for segment, tokens in zip(segments, buckets):
        if segment.get('text_source') != 'manual':
            segment['text'] = ''.join(tokens).strip()
            segment['text_source'] = 'asr' if tokens else ''
