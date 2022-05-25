import re
import aiohttp
import aiofiles
import asyncio
import json
import os
from fastapi import FastAPI
from aiohttp import ClientSession

title_re = re.compile("<title>(.*?)</title>", re.DOTALL)
cost_re = re.compile(r'"current_retail\\\":(.*?),')
desc_re = re.compile(r'"downstream_description\\\":\\\"(.*?)\\')
app = FastAPI()


class SalesTax:
    def __init__(self):
        self.base_path = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
        self.json_path = os.path.join(self.base_path, "data", "salestax.json")

    async def json_obj(self) -> float:
        with open(self.json_path) as jobj:
            data = json.load(jobj)
            for i in data:
                if i['State'] == "Colorado":
                    tr = i['State Tax Rate']
                    break
                else:
                    tr = 0.000
        return tr


async def tax_multiple(tax: float, price: float) -> float:
    cost = (tax * price) + price
    return cost


async def get_item(url: str, session: ClientSession) -> str:
    resp = await session.request(method="GET", url=url)
    resp.raise_for_status()
    print(f"Got Status Code: {resp.status}")
    html = await resp.text()
    return html


async def parse(url: str, session: ClientSession) -> dict:
    found = dict()
    found[asyncio.current_task().get_name()] = {}
    try:
        html_resp = await get_item(url=url, session=session)
    except (
            aiohttp.ClientError,
            aiohttp.http.HttpProcessingError,
    ) as e:
        print(f"Error {e}")
        return found
    else:
        for item in title_re.findall(html_resp):
            found[asyncio.current_task().get_name()].update({"name": item})
        for price in cost_re.findall(html_resp):
            found[asyncio.current_task().get_name()].update({"price": float(price)})
        for desc in desc_re.findall(html_resp):
            found[asyncio.current_task().get_name()].update({"description": desc})
    if found:
        pass
    else:
        found.update("Empty")
    return found


async def write(url: str, file: str, tax_rate: float, session: ClientSession) -> dict:
    here = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
    save_path = os.path.join(here, 'data', f'{file}.json')
    res = await parse(url=url, session=session)
    if not res:
        return {"Status": 500}
    else:
        price_with_tax = await tax_multiple(price=float(res[asyncio.current_task().get_name()]["price"]), tax=tax_rate)
        res[asyncio.current_task().get_name()].update({"tax": tax_rate, "price_with_tax": round(price_with_tax, 2)})
        print(res)
        async with aiofiles.open(save_path, 'a') as afile:
            await afile.write(json.dumps(res, indent=4))
            await afile.flush()
        return {"Status": 200}


async def bulk_read_write(url_file: str, file: str) -> None:
    here = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
    url_path = os.path.join(here, 'data', f'{url_file}.txt')
    _urls = None
    tax_rate = await SalesTax().json_obj()
    async with ClientSession() as session:
        tasks = []
        with open(url_path, "r") as infile:
            _urls = set(map(str.strip, infile))
        for urls in _urls:
            tasks.append(write(file=file, url=urls, session=session, tax_rate=tax_rate))
        await asyncio.gather(*tasks)
    print("Done")


@app.get("/items/")
async def main(url_file: str, file: str) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        print(loop)
        loop.create_task(bulk_read_write(url_file=url_file, file=file))
    else:
        asyncio.run(bulk_read_write(url_file=url_file, file=file))


@app.delete("/items/delete/")
async def remove_file(file: str) -> dict:
    here = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
    url_path = os.path.join(here, 'data', f'{file}.json')
    if os.path.isfile(url_path):
        try:
            os.remove(url_path)
            assert not os.path.isfile(url_path)
        except AssertionError as ae:
            return {"Status": 500, "Message": ae}
    else:
        return {"Status": 200, "Message": "No File Found"}
    return {"Status": 200, "Message": "File Deleted"}


@app.put("/items/add/")
async def add_url(url_file: str, url: str) -> dict:
    here = os.path.abspath(os.path.dirname(os.path.relpath(__file__)))
    url_path = os.path.join(here, 'data', f'{url_file}.txt')
    if os.path.isfile(url_path):
        async with aiofiles.open(url_path, 'a') as infile:
            await infile.write(f"\n{url}")
            await infile.flush()
    else:
        return {"Status": 500, "Message": "File Not Found"}
    return {"Status": 200, "Message": "URL added to file"}
