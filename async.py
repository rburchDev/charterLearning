'''import random
import asyncio
import time

c = (
    "\033[0m",
    "\033[36m",
    "\033[91m",
    "\033[35m",
)


async def makerandom(idx: int, threshold: int = 6) -> int:
    print(c[idx + 1] + f"Initiated makerandom({idx})")
    i = random.randint(0, 10)
    while i <= threshold:
        print(c[idx + 1] + f"makerandom({idx}) == {i} too low, retrying...")
        await asyncio.sleep(idx + 1)
        i = random.randint(0, 10)
    print(c[idx + 1] + f"...Finished makerandom({idx} == {i})" + c[0])
    return i


async def main():
    res = await asyncio.gather(*(makerandom(i, 10 - i - 1) for i in range(3)))
    return res


if __name__ == "__main__":
    random.seed(44)
    r1, r2, r3 = asyncio.run(main())
    print(f"\nr1: {r1}\nr2: {r2}\nr3: {r3}")'''

'''import asyncio
import random
import time
import sys


async def part1(n: int) -> str:
    i = random.randint(0, 10)
    print(f"part1 {n} sleeping for {i} seconds")
    await asyncio.sleep(i)
    result = f"result{n}-1"
    print(f"Returning part1 {n} == {result}")
    return result


async def part2(n: int, arg: str) -> str:
    i = random.randint(0, 10)
    print(f"part2 {n, arg} sleeping for {i} seconds")
    await asyncio.sleep(i)
    result = f"result{n}-2 derived from {arg}"
    print(f"Returning part2{n, arg} == {result}")
    return result


async def chain(n: int) -> None:
    start = time.perf_counter()
    p1 = await part1(n)
    p2 = await part2(n, p1)
    end = time.perf_counter() - start
    print(f"...Chained result{n} => {p2} took {end} seconds")


async def main(*args):
    await asyncio.gather(*(chain(n) for n in args))


if __name__ == "__main__":
    random.seed(444)
    args = [1, 2, 3] if len(sys.argv) == 1 else map(int, sys.argv[1:])
    start = time.perf_counter()
    asyncio.run(main(*args))
    end = time.perf_counter() - start
    print(f"Program finished in {end} seconds")'''


import asyncio
import logging
import re
import sys
import urllib.error
import urllib.parse
import aiofiles
import aiohttp
import os
import time
from typing import IO
from aiohttp import ClientSession
from abc import ABC


class Base(ABC):
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    logger = logging.getLogger("areq")
    logging.getLogger("chardet.charsetprober").disabled = True

    def __init__(self):
        self.HREF_RE = re.compile(r'href="(.*?)"')
        self.base_path = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))


class Crawler(Base):
    def __init__(self):
        super().__init__()

    def clean_up(self):
        if os.path.isfile(os.path.join(self.base_path, "foundurls.txt")):
            try:
                self.logger.info("File found, removing...")
                os.remove(os.path.join(self.base_path, "foundurls.txt"))
                assert not os.path.isfile(os.path.join(self.base_path, "foundurls.txt"))
            except AssertionError as ae:
                self.logger.exception(f"File not removed correctly... {ae}")
                pass
        else:
            self.logger.info("File not found...")
            pass

    async def fetch_html(self, url: str, session: ClientSession, **kwargs) -> str:
        self.logger.debug(f"Current Task Count in fetch_html: {len(asyncio.all_tasks())}")
        self.logger.debug(f"Current Task: {asyncio.current_task()}")
        resp = await session.request(method="GET", url=url, **kwargs)
        resp.raise_for_status()
        self.logger.info(f"Got response {resp.status} for URL: {url}")
        html = await resp.text()
        return html

    async def parse(self, url: str, session: ClientSession, **kwargs) -> set:
        self.logger.debug(f"Current Task Count in parse: {len(asyncio.all_tasks())}")
        self.logger.debug(f"Current Task: {asyncio.current_task()}")
        found = set()
        try:
            html = await self.fetch_html(url=url, session=session, **kwargs)
        except (
                aiohttp.ClientError,
                aiohttp.http.HttpProcessingError,
        ) as e:
            self.logger.error(f'aiohttp exception {url} [{getattr(e, "status", None)}]: {getattr(e, "message", None)}')
            return found
        except Exception as e:
            self.logger.exception(f'Non-aiohttp exception occured: {getattr(e, "__dict__", {})}')
            return found
        else:
            for link in self.HREF_RE.findall(html):
                try:
                    abslink = urllib.parse.urljoin(url, link)
                except (
                        urllib.error.URLError,
                        ValueError,
                ):
                    self.logger.exception(f"Error parsing URL: {link}")
                    pass
                else:
                    found.add(abslink)
            self.logger.info(f"Found {len(found)} links for {url}")
            return found

    async def write_one(self, file: IO, url: str, **kwargs) -> None:
        self.logger.debug(f"Current Task Count in write_one: {len(asyncio.all_tasks())}")
        self.logger.debug(f"Current Task: {asyncio.current_task()}")
        res = await self.parse(url=url, **kwargs)
        if not res:
            return None
        async with aiofiles.open(file, "a") as f:
            for p in res:
                await f.write(f"{url}\t{p}\n")
            self.logger.info(f"Wrote results for source URL: {url}")

    async def bulk_crawl_and_write(self, file: IO, url_: set, **kwargs) -> None:
        async with ClientSession() as session:
            tasks = []
            for url in url_:
                self.logger.debug(f"Adding {url} to task")
                tasks.append(
                    self.write_one(file=file, url=url, session=session, **kwargs)
                )
                # self.logger.debug(f"Current Task Count: {len(asyncio.all_tasks())}")
            t1 = time.perf_counter()
            await asyncio.gather(*tasks)
            self.logger.debug(f"Active Task: {len([task for task in asyncio.all_tasks() if not task.done()])}")
            self.logger.info(f"Time Elapsed: {time.perf_counter() - t1}")


if __name__ == "__main__":
    cl = Crawler()
    cl.clean_up()
    assert sys.version_info >= (3, 7), "Script requires Python 3.7 or greater"
    here = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
    with open(os.path.join(here, "urls.txt")) as infile:
        urls = set(map(str.strip, infile))
    outpath = os.path.join(here, "foundurls.txt")
    with open(outpath, "w+") as outfile:
        outfile.write("source_url\tparsed_url\n")
    asyncio.run(cl.bulk_crawl_and_write(file=outpath, url_=urls))  # type: IO[str]
