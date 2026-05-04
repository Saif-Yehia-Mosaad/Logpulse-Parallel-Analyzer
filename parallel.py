import multiprocessing
import time
import re
from collections import Counter, defaultdict


def parse_log(path):
    pattern = r"\[(.*?)\] (\w+): (.*)"
    errors = []

    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = re.match(pattern, line)
            if m:
                t, lvl, msg = m.groups()
                if lvl == "ERROR":
                    errors.append((t, msg))

                    # نفس الحمل الصناعي
                    for _ in range(15000):
                        x = hash(msg)
                        x = x * x

    return errors


def analyze(errors):
    msgs = [m for _, m in errors]
    c = Counter(msgs)

    freq = defaultdict(int)
    for t, _ in errors:
        minute = t[:16]
        freq[minute] += 1

    return len(errors), dict(c.most_common(3)), dict(freq)


def worker(path):
    return parse_log(path)


def run_parallel(files):
    start = time.perf_counter()

    with multiprocessing.Pool() as pool:
        results = pool.map(worker, files)

    all_errors = []
    for r in results:
        all_errors.extend(r)

    total, common, freq = analyze(all_errors)

    return {
        "time": time.perf_counter() - start,
        "total": total,
        "common": common,
        "freq": freq
    }