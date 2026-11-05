import copy
import json
import os
from pathlib import Path
import re
import threading
from datetime import datetime


def now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.courses = root / 'courses'
        self.courses.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def folder(self, course_id):
        if not re.fullmatch(r'[a-f0-9]{32}', course_id):
            raise FileNotFoundError('找不到这份音频。')
        return self.courses / course_id

    def load(self, course_id):
        with self.lock:
            path = self.folder(course_id) / 'course.json'
            return json.loads(path.read_text('utf-8'))

    def save(self, course):
        with self.lock:
            folder = self.folder(course['id'])
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / 'course.json'
            tmp = folder / 'course.json.tmp'
            course['updated'] = now()
            tmp.write_text(json.dumps(course, ensure_ascii=False), 'utf-8')
            os.replace(tmp, path)

    def update(self, course_id, change):
        with self.lock:
            course = self.load(course_id)
            change(course)
            self.save(course)
            return copy.deepcopy(course)

    def library(self):
        result = []
        with self.lock:
            for p in self.courses.glob('*/course.json'):
                try:
                    c = json.loads(p.read_text('utf-8'))
                    result.append({key: c.get(key) for key in ['id','title','duration','created','updated','source_id','source_url','current']}
                                  | dict(total=len(c['segments']), done=sum(s.get('done',False) for s in c['segments']),
                                         transcribed=bool(c.get('words'))))
                except (ValueError, OSError, KeyError):
                    continue
        return sorted(result, key=lambda c: c.get('created',''), reverse=True)
