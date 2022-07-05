import requests
import json
import os
from dotenv import load_dotenv
import hashlib
from datetime import datetime
import pytz

load_dotenv()


local_tz = pytz.timezone("Asia/Tehran")
now = datetime.now(local_tz).date()
FILE_NAME = ".data/" + str(now) + ".json"

TOMAN_FORMATTER = "{:,}"
LAT = os.getenv("LAT")
LONG = os.getenv("LONG")
URL = "https://foodparty.zoodfood.com/676858d198d35e7713a47e66ba0755c8/mobile-offers/{LAT}/{LONG}?lat={LAT}&long={LONG}&optionalClient=WEBSITE&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1&front_id=food-party-100288&page=0&superType=1&segments=%7B%7D&locale=fa"

# get data from api
def get_data(url):
    response = requests.get(url)
    data = response.json()
    return data

products = get_data(URL)["data"]["products"]

try:
    with open(FILE_NAME, "r", encoding="UTF-8") as f:
        db = json.load(f)
except FileNotFoundError:
    db = []

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
            continue
        else:
            db.append(PRODUCT_HASH)

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
with open(FILE_NAME, "w", encoding="UTF-8") as f:
    json.dump(db, f)
