# Goshne

[داکیومنت فارسی](README_FA.md)

Welcome to Goshne! Your new best friend in the quest for delicious deals. We dive into the depths of the [Snappfood](https://snappfood.ir/) website, wrestle with discounts (Food party and other parties), and deliver them straight to your Telegram (in your private messages or a Telegram channel of your choice). Perfect for all the foodie adventurers and bargain ninjas out there! Get ready to discover mouth-watering deals and share the joy with your network. Let the food hunt begin!

<img src="resource/screenshot.png" alt="screenshot of Goshne in action" width="33%" />

## Installation

Follow these steps to get Goshne up and running:

### Clone the repository

Start by cloning the Goshne repository to your local machine. You can do this by running the following command in your terminal:

```bash
git clone https://github.com/ahbanavi/goshne.git
```

### Copy and modify the configuration file

Next, navigate to the `config` directory and make a copy of the `config.local.yaml.example` file. Rename the copy to `config.local.yaml`.

```bash
cd goshne/config
cp config.local.yaml.example config.local.yaml
```

Open `config.local.yaml` in your favorite text editor and replace the placeholder values with your actual values. Refer to the [Configuration](#configuration) section for more details.

### Run Goshne

#### With Docker

Navigate back to the root directory of the project and run the following command to start Goshne:

```bash
cd ..
docker compose up -d # or `docker-compose up -d` for older versions
```

Goshne is now up and running with Docekr!

P.S.: The only reason I instruct to clone the repository is to get the `config.local.yaml.example` and `docker-compose.yaml` files. If you prefer to not clone the repository, you can only download these two files and change the bind `volumes` in `docker-compose.yaml` to correct paths. The docker image is available on [Github Packages](https://github.com/ahbanavi/goshne/pkgs/container/goshne)

#### With Python

If you prefer to run Goshne without Docker, follow these steps:

1. Navigate back to the root directory of the project:

```bash
cd ..
```

2. Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate # For Linux and macOS, or use `venv\Scripts\activate.bat` for windows cmd and `venv\Scripts\Activate.ps1` for powershell.
```

3. Install the required Python packages:

```bash
pip3 install -r requirements.txt
```

4. Run Goshne:

```bash
python3 main.py
```

Goshne is now up and running, you can cancel it with `Ctrl+C` at any time.

## Configuration

The application's configuration is handled by `config.local.yaml.example`. To use it, copy the file and rename it to `config.local.yaml`.

Here's a brief explanation of the configuration parameters:

```yaml
telegram:
    token: token # Your Telegram bot token. This is required and should be a string.
    endpoint: https://api.telegram.org/bot # The endpoint for Telegram bot API server. This is optional and defaults to https://api.telegram.org/bot. Your bot token will be appended to this.

schedule:
    mins: 15 # The interval in minutes at which the bot will check for discounts.

timeout: 10 # The timeout in seconds for HTTP requests. This is optional and defaults to 10 seconds.

peoples: # At least one person is required.
    person_name: # The name of a person to send deals to. It can be anything you want and doesn't have any effect on the bot's functionality, but should be unique and string.
        chat_id: chat_id # The telegram chat id that the bot will send deals to. This is required and should be integer, you can find it with the help of https://t.me/username_to_id_bot.
        lat: lat # The latitude for the person's location. This is required.
        long: long # The longitude for the person's location. This is required.
        threshold: 30 # The discount threshold. This is optional and defaults to 0. If set, the bot will only send deals with a discount greater than or equal to this value.


    # More people can be added here in the same format as above.
```

Replace `token`, `person_name`, `chat_id`, `lat`, `long`, and `threshold` with your actual values.
