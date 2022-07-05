import requests
import json
import os
from dotenv import load_dotenv
import hashlib
from datetime import datetime, timedelta
import pytz
from sqlitedict import SqliteDict

load_dotenv()

local_tz = pytz.timezone("Asia/Tehran")
now = datetime.now(local_tz).date()
FILE_NAME = ".data/" + str(now) + ".json"

TOMAN_FORMATTER = "{:,}"
LAT = os.getenv("LAT")
LONG = os.getenv("LONG")
URL = f"https://foodparty.zoodfood.com/676858d198d35e7713a47e66ba0755c8/mobile-offers/{LAT}/{LONG}?lat={LAT}&long={LONG}&optionalClient=WEBSITE&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1&front_id=food-party-100288&page=0&superType=1&segments=%7B%7D&locale=fa"

# get data from api
def get_data(url):
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "DNT": "1",
        "Host": "foodparty.zoodfood.com",
        "Origin": "https://snappfood.ir",
        "Referer": "https://snappfood.ir",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    return data


products = get_data(URL)["data"]["products"]

db = SqliteDict("db.sqlite")

for product in products:
    if product["discountRatio"] >= int(os.getenv("DISCOUNT_THRESHOLD")):
        priceAfterDiscount = product["price"] * (100 - product["discountRatio"]) / 100

        # make hash based on title, price after discount and vendortitle
        PRODUCT_HASH = hashlib.md5(
            product["title"].encode("utf-8")
            + str(priceAfterDiscount).encode("utf-8")
            + product["vendorTitle"].encode("utf-8")
        ).hexdigest()
        # check if product is already in db
        if PRODUCT_HASH in db:
            if datetime.now(local_tz) - db[PRODUCT_HASH]["time"] < timedelta(days=1):
                continue
            else:
                db[PRODUCT_HASH] = {
                    "time": datetime.now(local_tz),
                }
        else:
            db[PRODUCT_HASH] = {
                "time": datetime.now(local_tz),
            }

        url = "https://snappfood.ir/restaurant/menu/" + product["vendorCode"]
        out = "[" + product["title"] + "](" + url + ")\n"
        out += product["vendorTypeTitle"] + " " + product["vendorTitle"] + "\n"
        out += "تخفیف: " + str(product["discountRatio"]) + "%\n"
        out += "قیمت: " + TOMAN_FORMATTER.format(product["price"]) + " تومان\n"
        out += (
            "با تخفیف: " + TOMAN_FORMATTER.format(int(priceAfterDiscount)) + " تومان\n"
        )
        out += (
            "هزینه ارسال: "
            + TOMAN_FORMATTER.format(int(product["deliveryFee"]))
            + " تومان\n"
        )
        out += (
            "امتیاز: "
            + str(product["rating"])
            + " از "
            + str(product["vote_count"])
            + " رای \n"
        )
        out += "باقیمانده: " + str(product["remaining"]) + "\n"

        # send photo
        requests.post(
            "https://api.telegram.org/bot"
            + os.getenv("TELEGRAM_BOT_API")
            + "/sendPhoto",
            data={
                "chat_id": os.getenv("CHAT_ID"),
                "photo": product["image"],
                "caption": out,
                "parse_mode": "Markdown",
            },
        )

# store db
db.commit()
db.close()
