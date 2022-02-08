from User import User
from Battle import Battle
from Page import Page

from dotenv import load_dotenv
from time import sleep
from random import randint, uniform
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

from rich.traceback import install
from rich.console import Console

import os
import sys
import traceback
import json
import requests

# setup default rich traceback (pretty print)
install()
console = Console()
# green = success
# red = failure
# white = main
# magenta = page
# blue = user
# yellow = battle


# load .env variables
load_dotenv(override=True)

# load card details
CARDS_DETAILS = []
with console.status(
    "[bold white]Obtaining all card information...", spinner="toggle10"
) as status:
    sleep(randint(2, 4))
    CARDS_DETAILS = json.loads(
        requests.get("https://api.splinterlands.io/cards/get_details").content
    )
console.log("[bold green]Card information loaded in")
sleep(randint(2, 4))

# load battlebase (previously logged battles database)
BATTLEBASE = []
with console.status(
    "[bold white]Booting up the battlebase connection...", spinner="betaWave"
) as status:
    sleep(randint(2, 4))
    with open("collection.json") as f:
        BATTLEBASE = json.load(f)
console.log("[bold green]Battlebase loaded")
sleep(randint(2, 4))

# gets global user details
USER = {
    "username": os.getenv("USERNAME").lower(),
    "email": os.getenv("EMAIL"),
    "password": os.getenv("PASSWORD"),
    "claim_reward_quest": os.getenv("CLAIM_REWARD_QUEST").lower() == "true" or False,
    "claim_reward_season": os.getenv("CLAIM_REWARD_SEASON").lower() == "true" or False,
}

# get global browser details
play = sync_playwright().start()
creation = datetime.now()

BROWSER = {
    "base_url": "https://splinterlands.com",
    "headless": os.getenv("HEADLESS").lower() == "true",
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--single-process",
        "--hide-scrollbars",
        "--mute-audio",
        "--disable-web-security",
    ],
    "creation": creation,
    "lifespan": randint(15, 20),  # minutes
}

p_browser = play.chromium.launch_persistent_context(
    "./", headless=BROWSER["headless"], args=BROWSER["args"]
)
BROWSER["browser"] = p_browser

# get global battle details
BATTLE = {
    "card_details": CARDS_DETAILS,
    "battle_interval": int(os.getenv("BATTLE_INTERVAL")),
    "ecr_min": float(int(os.getenv("ECR_MIN")) / 100),
    "ecr_max": float(int(os.getenv("ECR_MAX")) / 100),
    "prioritize_quest": os.getenv("PRIORITIZE_QUEST").lower() == "true",
}


def main():
    try:
        # Step 0: Build Page
        page = Page(console, BROWSER)
        sleep(uniform(1, 2))

        browser_status = True

        # Step 1: Setup Player
        player = User(console, USER)
        sleep(uniform(1, 2))

        while True:
            try:
                # Step 2: Checks if player is logged in; if not, logs them in
                with console.status(
                    "[bold white]Checking if player is logged in"
                ) as status:
                    player_login_status = page.is_logged_in(player.username)
                    sleep(randint(1, 3))

                if not player_login_status:
                    console.log("[bold white]Currently logged out")
                    page.logout_account()

                    # Step 2.1: Attempts to login player
                    with console.status(
                        "[bold blue]Attempting to login", spinner="arrow3"
                    ) as status:
                        player_login = page.login(player)
                        sleep(1)

                    if player_login == None:
                        console.log("[bold red]Login attempt failed :x:")
                        sleep(randint(3, 5))
                        break
                    else:
                        console.log(
                            "[bold green]Login attempt successful :white_check_mark:"
                        )
                else:
                    console.log("[bold white]Currently logged in")
                sleep(1)

                for _ in range(2):
                    page.close_modal()

                # Step 3: Check if player is already in battle
                if not page.is_mid_battle():
                    # Step 3.1: Calculate how long we should wait for ECR to reset
                    ecr_wait = 0
                    with console.status(
                        "[bold white]Calculating Current ECR"
                    ) as status:
                        ecr_wait = page.calculate_ecr_wait(
                            BATTLE["ecr_min"], BATTLE["ecr_max"]
                        )

                    if ecr_wait > 0:
                        # Step 3.2: If have to wait, close browser and user data
                        BROWSER["browser"].close()

                        with console.status(
                            "[bold white]Waiting "
                            + str((ecr_wait / 60) / 60)
                            + " Hours",
                            spinner="pong",
                        ) as status:
                            sleep(ecr_wait)

                        p_browser = play.chromium.launch(
                            headless=BROWSER["headless"], args=BROWSER["args"]
                        )
                        BROWSER["browser"] = p_browser
                        page = Page(console, BROWSER)
                        sleep(uniform(1, 2))
                        continue
                    else:
                        for _ in range(2):
                            page.close_modal()

                # Step 4: Initiate battle
                with console.status(
                    "[bold white]Initiating battle", spinner="shark"
                ) as status:
                    battle_initiation = page.initiate_battle()

                if not battle_initiation:
                    console.log(
                        "[bold red] Something occurred during battle initiation"
                    )
                    break

                sleep(randint(1, 3))

                # Step 5 Create battle instance with battle details
                with console.status("[bold white]Getting battle details") as status:
                    battle_details = page.get_battle_details()
                    sleep(1)

                battle = Battle(
                    console, player, CARDS_DETAILS, battle_details, BATTLEBASE
                )

                # Step 6: Choose deck from battle deck logs
                with console.status(
                    "[bold white]Picking deck", spinner="growVertical"
                ) as status:
                    deck = battle.get_deck(BATTLE["prioritize_quest"])
                console.log("[bold green]Deck selected")
                sleep(uniform(1, 2))

                # Step 7: Click cards on the page
                page.click_cards(deck)

                # Step 8: Start the battle on the page
                page.start_battle()

                # Step 9: Check who won the battle
                winner = battle.check_winner()

                if winner == USER["username"]:
                    console.log("[bold green]Winner: " + winner)
                    player.battles_won += 1
                else:
                    console.log("[bold red]Winner: " + winner)
                player.battles_played += 1

                # Step 9: Attempts to claim rewards
                # if (
                #     CLAIM_REWARD_QUEST
                #     and player.quest["claimed"] == None
                #     and player.quest["quest_total"] == player.quest["completed_total"]
                # ):
                #     page.claim_reward("quest")
                # if CLAIM_REWARD_SEASON:
                # page.claim_reward("season")

                console.log("Battles Played: " + str(player.battles_played))
                sleep(uniform(1, 2))
                console.log("Battles Won: " + str(player.battles_won))
                sleep(uniform(1, 2))
            except Exception:
                console.print_exception(show_locals=True)
                console.log("[bold red]Error Occurred During Battle Process")
                del page
                BROWSER["browser"].close()
                browser_status = False
            # Step 10: Sleep for set interval
            console.log("Resting: " + str(BATTLE["battle_interval"]) + " Seconds")

            # Step 10.1: Close browser if older than browser_life_allowed minutes or was closed
            if (
                BROWSER["creation"]
                < datetime.now() - timedelta(minutes=BROWSER["lifespan"])
                and browser_status != False
            ):
                del page
                BROWSER["browser"].close()
                browser_status = False

            sleep(BATTLE["battle_interval"])

            # Step 10.2: Open browser if old one was closed
            if browser_status == False:
                p_browser = play.chromium.launch(
                    headless=BROWSER["headless"], args=BROWSER["args"]
                )
                browser_status = True

                BROWSER["browser"] = p_browser
                BROWSER["creation"] = datetime.now()

                page = Page(console, BROWSER)
                sleep(uniform(1, 2))
    except KeyboardInterrupt:
        with console.status("[bold status]Shutdown requested...") as status:
            sleep(3)
    except:
        console.print_exception(show_locals=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
