import asyncio
import logging
import os
import os.path

import aiohttp
from selenium import webdriver

LOG = logging.getLogger("Search")
NOT_FOUND = "I didn't find anything :("

TMP_DIR = os.path.join(__file__, os.pardir, os.pardir, os.pardir, "tmp")
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

def googleimg(query):
    img_path = os.path.join(TMP_DIR, "googleimg.png")

    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--log-level=3")
        driver = webdriver.Chrome(options=chrome_options)
        url = "https://www.google.com/search?tbm=isch&q={}".format(
            query.replace(" ", "+"))
        LOG.info("Searching for %s", query)
        driver.get(url)

        # Scroll to the top edge of image results
        driver.execute_script("window.scrollTo(0, 120)") 
        driver.save_screenshot(img_path)
        driver.quit()

        LOG.info("Uploading...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(upload(img_path))

    except Exception as exception:  # pylint: disable=W0703
        LOG.info("Cannot google image search with '%s'", query)
        LOG.exception(exception)
        return NOT_FOUND

async def upload(file_path):
    headers = {}
    with aiohttp.MultipartWriter() as mpwriter:
        part = mpwriter.append(open(file_path, "rb"))
        part.headers["Content-Disposition"] = (
            "form-data; name='attachment'; "
            f"filename='{os.path.basename(file_path)}'")
        part.headers["Content-Type"] = "image/png"

    headers["Content-Type"] = ("multipart/form-data; "
                               f"boundary={mpwriter.boundary}")

    async with aiohttp.request("post",
                               "https://i.nuuls.com/upload",
                               params={"password": "ayylmao"},
                               data=mpwriter,
                               headers=headers) as r:
        text = await r.text()
        return text
