'''import requests
import multiprocessing
import time


class MProcess:
    def __init__(self):
        self.session = None

    def set_global_session(self):
        print("Running global")
        if not self.session:
            self.session = requests.Session()

    def download_site(self, url):
        print("Running download sites")
        with self.session.get(url) as resp:
            name = multiprocessing.current_process().name
            print(f"{name}:READ {len(resp.content)} from {url}")

    def download_all_sites(self, s):
        print("Running download all")
        with multiprocessing.Pool(initializer=self.set_global_session) as pool:
            pool.map(self.download_site, s)


if __name__ == "__main__":
    sites = [
        "https://www.jython.org",
        "https://github.com/rburchDev",
    ] * 80
    s_time = time.time()
    cl = MProcess()
    cl.set_global_session()
    cl.download_all_sites(sites)
    f_time = time.time()
    print(f"Downloaded {len(sites)} in {f_time - s_time} seconds")'''

'''import requests
import multiprocessing
import time

session = None


def set_global_session():
    global session
    if not session:
        session = requests.Session()


def download_site(url):
    with session.get(url) as response:
        name = multiprocessing.current_process().name
        print(f"{name}:Read {len(response.content)} from {url}")


def download_all_sites(sites):
    with multiprocessing.Pool(initializer=set_global_session) as pool:
        pool.map(download_site, sites)


if __name__ == "__main__":
    sites = [
        "https://www.jython.org",
        "http://olympus.realpython.org/dice",
    ] * 80
    start_time = time.time()
    download_all_sites(sites)
    duration = time.time() - start_time
    print(f"Downloaded {len(sites)} in {duration} seconds")'''

import time
import multiprocessing


class ProcessCPU:
    def __init__(self):
        self.numbers = [5000000 + x for x in range(20)]

    @staticmethod
    def cpu_bound(num):
        print(multiprocessing.current_process())
        return sum(i * i for i in range(num))

    def find_sums(self):
        with multiprocessing.Pool() as pool:
            pool.map(self.cpu_bound, self.numbers)


if __name__ == "__main__":
    s_time = time.time()
    cl = ProcessCPU()
    cl.find_sums()
    f_time = time.time()
    print(f"Duration: {f_time - s_time}")