import hashlib
import json
import random
import sys
import time
from datetime import datetime, timedelta

import pytz
import requests
import schedule
import yaml
from sqlitedict import SqliteDict

local_tz = pytz.timezone("Asia/Tehran")

TOMAN_FORMATTER = "{:,}"
TEST = len(sys.argv) > 1 and sys.argv[1] == "-t"

# load emojist from resource/food-emojis.json
with open("resource/food-emojis.json", encoding="UTF-8") as f:
    FOOD_EMOJIS = json.load(f)

HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "DNT": "1",
    "Origin": "https://snappfood.ir",
    "Referer": "https://snappfood.ir",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "TE": "trailers",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",  # noqa
}

# read config from yaml
try:
    with open("config/config.local.yaml", "r", encoding="UTF-8") as f:
        CONFIG = yaml.load(f, Loader=yaml.FullLoader)
except FileNotFoundError:
    print("❗️ ERR: config.local.yaml not found")
    sys.exit(1)

db = SqliteDict("storage/db.sqlite")


def get_and_send(name, lat, long, chat_id, threshold=0, timeout=10):
    """get data from snapp based on inputs and send to telegram

    Args:
        name (string): name of person, used for creating hash
        lat (string): latitude
        long (string): longitude
        chat_id (int): telegram chat id to send to
        threshold (int, optional): threshold for getting discounts, default is 0
        timeout (int, optional): http timeout in seconds, default is 10
    """
    home_url = f"https://snappfood.ir/search/api/v1/desktop/new-home?lat={lat}&long={long}&optionalClient=WEBSITE&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1&locale=fa"

    # get home page
    HEADERS["Host"] = "snappfood.ir"
    print(f"🕒 Downloading Offers for {name}")
    home_page = requests.get(home_url, headers=HEADERS, timeout=timeout)
    if home_page.status_code != 200:
        print(f"❗️ ERR: {home_page.status_code}")
        if home_page.status_code == 403:
            print(
                "❗️ ERR: Our IP Address is blocked by Snappfood, please change your IP Address and try again"
            )
            exit(254)
        return False
    home_data = home_page.json()
    if "error" in home_data:
        print(f"❗️ ERR: {home_data['error']}")
        return False

    if home_data["data"]["result"][1]["id"] != 8:
        return False

    # get party_url
    party_url = home_data["data"]["result"][1]["data"]["url"]

    # override Host header based on party_url
    HEADERS["Host"] = party_url.split("/")[2]
    print("🕕 Extracting Party Foods")
    response = requests.get(party_url, headers=HEADERS, timeout=timeout).json()
    if "error" in response:
        print(f"❗️ ERR: {response['error']}")
        return False

    party_title = response["data"]["title"]
    # extract hashtag, replace all none words with _
    party_hashtag = "#" + "\_".join(party_title.split())

    products = response["data"]["products"]

    for product in products:
        if product["discountRatio"] >= threshold:
            discount_price = product["price"] * (100 - product["discountRatio"]) / 100

            product_hash = hashlib.md5(
                name.encode("utf-8")
                + product["title"].encode("utf-8")
                + str(discount_price).encode("utf-8")
                + product["vendorTitle"].encode("utf-8")
            ).hexdigest()

            if not TEST and product_hash in db:
                if datetime.now(local_tz) - db[product_hash]["time"] < timedelta(hours=12):  # fmt: skip
                    continue
                else:
                    db[product_hash] = {
                        "time": datetime.now(local_tz),
                    }
            else:
                db[product_hash] = {
                    "time": datetime.now(local_tz),
                }

            vendor_url = "https://snappfood.ir/restaurant/menu/" + product["vendorCode"]
            # fmt: off
            out = random.choice(FOOD_EMOJIS) + " " + party_hashtag + " [" + product["title"] + "](" + vendor_url+ ")\n" # noqa
            out += "🍽 " + product["vendorTypeTitle"] + " " + product["vendorTitle"] + "\n"
            out += "🛍 ‏*" + str(product["discountRatio"]) + "%*\n"
            out += "💵 *" + TOMAN_FORMATTER.format(product["price"]) + "* ت\n"
            out += "💸 *" + TOMAN_FORMATTER.format(int(discount_price)) + "* ت (" + TOMAN_FORMATTER.format(int(product["price"] - discount_price)) + "-)\n" # noqa
            out += "🛵 *" + TOMAN_FORMATTER.format(int(product["deliveryFee"])) + "* ت\n"
            out += "⭐️ " + str(round(product["rating"], 2)) + " از " + str(product["vote_count"]) + " رای \n"
            out += "⌛ ‏" + str(product["remaining"]) + "\n"
            # fmt: on
            print(f"📤 Sending {product['title']} to {name}")
            requests.post(
                CONFIG["telegram"].get("endpoint", "https://api.telegram.org/bot")
                + CONFIG["telegram"]["token"]
                + "/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "photo": product["main_image"]
                    or "https://raw.githubusercontent.com/ahbanavi/goshne/main/resource/default.jpg",  # default image
                    "caption": out,
                    "parse_mode": "Markdown",
                    # add inline button
                    "reply_markup": json.dumps(
                        {
                            "inline_keyboard": [
                                [
                                    {
                                        "text": "🛒 خرید",
                                        "url": vendor_url,
                                    }
                                ]
                            ]
                        }
                    ),
                },
                timeout=timeout,
            )

    print(f"🕘 Finished for {name}\n")


# for each person in config peoples get_and_send
def main():
    try:
        for person_name in CONFIG["peoples"]:
            person = CONFIG["peoples"][person_name]
            get_and_send(
                name=person_name,
                lat=person["lat"],
                long=person["long"],
                chat_id=person["chat_id"],
                threshold=person.get("threshold", 0),
                timeout=CONFIG.get("timeout", 10),
            )

            if TEST:
                break

        # store db
        db.commit()
    except Exception as ex:
        print(f"❗️ ERR: {ex}")
        return False


if TEST:
    main()

else:
    print(
        "Running app every %d minutes, with Http Timeout of %d seconds...\n"
        % (CONFIG["schedule"]["mins"], CONFIG.get("timeout", 10))
    )
    schedule.every(CONFIG["schedule"]["mins"]).minutes.do(main)

    # run once at start
    main()

    while 1:
        n = schedule.idle_seconds()
        if n is None:
            # no more jobs
            break
        elif n > 0:
            # sleep exactly the right amount of time
            time.sleep(n)
        schedule.run_pending()

db.close()
