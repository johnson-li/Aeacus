import os.path
from multiprocessing import Pool, Process
import time
import threading

import numpy as np
from ultralytics import YOLO

from aeacus import RESOURCE_PATH


def run(n):
    model = YOLO(os.path.join(RESOURCE_PATH, "yolov8n.pt"))
    _ = model(os.path.join(RESOURCE_PATH, "bus.jpg"))
    delays = []
    for i in range(10):
        ts = time.time()
        _ = model(os.path.join(RESOURCE_PATH, "bus.jpg"))
        delay = time.time() - ts
        delays.append(delay)
    print(f'[{n}] Delay: {np.median(delays)}\n')


class MyThread(threading.Thread):
    def __init__(self, n):
        super().__init__()
        self.n = n

    def run(self) -> None:
        run(self.n)


def main():
    for num in range(1, 20):
        threads = []
        for i in range(num):
            threads.append(MyThread(num))
        for p in threads:
            p.start()
        for p in threads:
            p.join()


if __name__ == '__main__':
    main()
