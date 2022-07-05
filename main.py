import requests
import json
import os
from dotenv import load_dotenv
import hashlib
from datetime import datetime, timedelta
import pytz
from sqlitedict import SqliteDict
import yaml
import sys

load_dotenv()

local_tz = pytz.timezone("Asia/Tehran")

TOMAN_FORMATTER = "{:,}"

HEADERS = {
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

# read config from yaml
try:
    with open("config.local.yaml", "r", encoding="UTF-8") as f:
        CONFIG = yaml.load(f, Loader=yaml.FullLoader)
except FileNotFoundError:
    print(
        "❗️ ERR: `config.local.yaml` not found, consider creating one based on `config.local.yaml.example`"
    )
    sys.exit(1)

db = SqliteDict("db.sqlite")


def get_and_send(name, lat, long, chat_id, threshold=0):
    url = f"https://foodparty.zoodfood.com/676858d198d35e7713a47e66ba0755c8/mobile-offers/{lat}/{long}?lat={lat}&long={long}&optionalClient=WEBSITE&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1&front_id=food-party-100288&page=0&superType=1&segments=%7B%7D&locale=fa"

    response = requests.get(url, headers=HEADERS).json()

    products = response["data"]["products"]

    for product in products:
        if product["discountRatio"] >= threshold:
            priceAfterDiscount = (
                product["price"] * (100 - product["discountRatio"]) / 100
            )

            PRODUCT_HASH = hashlib.md5(
                name.encode("utf-8")
                + product["title"].encode("utf-8")
                + str(priceAfterDiscount).encode("utf-8")
                + product["vendorTitle"].encode("utf-8")
            ).hexdigest()

            if PRODUCT_HASH in db:
                if datetime.now(local_tz) - db[PRODUCT_HASH]["time"] < timedelta(
                    days=1
                ):
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
                "با تخفیف: "
                + TOMAN_FORMATTER.format(int(priceAfterDiscount))
                + " تومان\n"
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
                + CONFIG["telegram"]["token"]
                + "/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "photo": product["image"],
                    "caption": out,
                    "parse_mode": "Markdown",
                },
            )


# for each person in config peoples get_and_send
for person_name in CONFIG["peoples"]:
    person = CONFIG["peoples"][person_name]
    get_and_send(
        name=person_name,
        lat=person["lat"],
        long=person["long"],
        chat_id=person["chat_id"],
        threshold=person.get("threshold", 0),
    )

# store db
db.commit()
db.close()
