'''import time
from threading import Thread, get_ident


def thread_obj(name):
    print(f"Thread started {name}")
    time.sleep(1)
    print(f"Thread ended {name}")


if __name__ == "__main__":
    t_start = time.time()
    print("start")
    threads = []
    for i in range(3):
        x = Thread(target=thread_obj, args=(i,), daemon=True)
        threads.append(x)
        x.start()
        print(f"Started Thread ID {get_ident()}")

    for i, thread in enumerate(threads):
        print(f"Before joining thread-{i}")
        thread.join()
        print(f"Thread-{i} done")
    t_end = time.time()
    total = t_end - t_start
    print(f"end {total}\n")'''

'''import time
import concurrent.futures
import threading


def thread_obj(name):
    print(f"Starting Thread ID {threading.get_ident()} and name {name}")
    time.sleep(1)
    print(f"Ending Thread ID {threading.get_ident()} and name {name}")


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as exe:
        exe.map(thread_obj, range(3))'''

'''import time
import concurrent.futures
import threading


class FakeDatabase:
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def update(self, name):
        print(f"STARTING: Thread ID {threading.get_ident()} and name {name}")
        with self._lock:
            print(f"LOCK: Thread ID {threading.get_ident()} and name {name}")
            local_copy = self.value
            local_copy += 1
            time.sleep(.5)
            self.value = local_copy
            print(f"R-LOCK: Thread ID {threading.get_ident()} and name {name}")
        print(f"ENDING: Thread ID {threading.get_ident()} and name {name}")


if __name__ == "__main__":
    db = FakeDatabase()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as exe:
        for i in range(2):
            exe.submit(db.update, i)
    print(f"Value is {db.value}")'''


import random
import time
import threading
import queue
import concurrent.futures


def producer(pl, evt):
    while not evt.is_set():
        message = random.randint(1, 101)
        print(f"Producer got message {message}")
        print(f"PRODUCER THREAD ID: {threading.get_ident()}")
        pl.put(message)
    print(f"Producer got EVT EXIT")


def consumer(pl, evt):
    while not evt.is_set() or not pl.empty():
        message = pl.get()
        print(f"Consumer storing message: {message} size={pl.qsize()}")
        print(f"CONSUMER THREAD ID: {threading.get_ident()}")
    print("Consumer got EVT EXIT")


if __name__ == "__main__":
    pipeline = queue.Queue(maxsize=10)
    event = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as exe:
        exe.submit(producer, pipeline, event)
        exe.submit(consumer, pipeline, event)
        time.sleep(1)
        print("MAIN: Setting event")
        event.set()
