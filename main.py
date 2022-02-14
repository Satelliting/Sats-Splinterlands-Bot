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
try:
    with console.status(
        "[bold blue]Obtaining all card information...", spinner="toggle10"
    ) as status:
        sleep(randint(2, 4))
        CARDS_DETAILS = json.loads(
            requests.get("https://api.splinterlands.io/cards/get_details").content
        )
    console.log("[bold white]Data Status: [bold green]Card information loaded")
except:
    console.print_exception()
    console.log("[bold white]Data Status: [bold red]Card information unable to loaded")
    sys.exit()
sleep(randint(2, 4))

# load battlebase (previously logged battles database)
BATTLEBASE = []
try:
    with console.status(
        "[bold blue]Booting up the battlebase connection...", spinner="betaWave"
    ) as status:
        sleep(randint(2, 4))
        with open("collection.json") as f:
            BATTLEBASE = json.load(f)
    console.log("[bold white]Battlebase Status: [bold green]Battlebase loaded")
except:
    console.print_exception()
    console.log("[bold white]Battlebase Status: [bold red]Battlebase unable to load")
    sys.exit()
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
                    "[bold blue]Checking if player is logged in"
                ) as status:
                    player_login_status = page.is_logged_in(player.username)
                    sleep(randint(1, 3))

                if not player_login_status:
                    console.log(
                        "[bold white]Login Status: [bold red]Currently logged out"
                    )
                    page.logout_account()

                    # Step 2.1: Attempts to login player
                    player_login = page.login(player)
                    sleep(1)

                    if player_login == None:
                        console.log("[bold red]Login attempt failed :x:")
                        sleep(randint(3, 5))
                        break
                    else:
                        console.log(
                            "[bold white] Login Status: [bold green]Login attempt successful :white_check_mark:"
                        )
                else:
                    console.log(
                        "[bold white]Login Status: [bold yellow]Currently logged in"
                    )
                sleep(1)

                # Step 3: Check if player is already in battle
                if not page.is_mid_battle():
                    # Step 3.1: Calculate how long we should wait for ECR to reset
                    ecr_wait = 0
                    with console.status("[bold blue]Calculating Current ECR") as status:
                        ecr_wait = page.calculate_ecr_wait(
                            BATTLE["ecr_min"], BATTLE["ecr_max"]
                        )

                    if ecr_wait > 0:
                        # Step 3.2: If have to wait, close browser and user data
                        BROWSER["browser"].close()

                        with console.status(
                            "[bold blue]Waiting "
                            + str((ecr_wait / 60) / 60)
                            + " Hours",
                            spinner="pong",
                        ) as status:
                            sleep(ecr_wait)

                        p_browser = play.chromium.launch_persistent_context(
                            "./", headless=BROWSER["headless"], args=BROWSER["args"]
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
                    "[bold blue]Initiating battle", spinner="shark"
                ) as status:
                    battle_initiation = page.initiate_battle()

                if not battle_initiation:
                    console.log("[bold red]Something occurred during battle initiation")
                    break

                sleep(randint(1, 3))

                # Step 5 Create battle instance with battle details
                with console.status("[bold blue]Getting battle details") as status:
                    battle_details = page.get_battle_details()
                    sleep(1)

                battle = Battle(
                    console, player, CARDS_DETAILS, battle_details, BATTLEBASE
                )

                # Step 6: Choose deck from battle deck logs
                with console.status(
                    "[bold blue]Picking deck", spinner="growVertical"
                ) as status:
                    deck = battle.get_deck(BATTLE["prioritize_quest"])
                sleep(uniform(1, 2))

                # Step 7: Click cards on the page
                page.click_cards(deck)

                # Step 8: Start the battle on the page
                page.start_battle()

                # Step 9: Check who won the battle
                winner = battle.check_winner()

                if winner == USER["username"]:
                    player.battle_streak += 1
                    console.log("[bold white]Winner: [bold green]" + winner)
                    player.battles_won += 1
                elif winner == "DRAW":
                    console.log("[bold white]Winner: [bold yellow]" + winner)
                    player.battles_drawn += 1
                else:
                    player.battle_streak = 0
                    player.battles_lost += 1
                    console.log("[bold white]Winner: [bold red]" + winner)
                player.battles_played += 1
                sleep(uniform(1, 2))

                # Step 9: Attempts to claim rewards
                # if (
                #     CLAIM_REWARD_QUEST
                #     and player.quest["claimed"] == None
                #     and player.quest["quest_total"] == player.quest["completed_total"]
                # ):
                #     page.claim_reward("quest")
                # if CLAIM_REWARD_SEASON:
                # page.claim_reward("season")

                console.log(
                    "[bold white]Battle Stats: [bold green]"
                    + str(player.battles_won)
                    + "[white]/[bold yellow]"
                    + str(player.battles_drawn)
                    + "[white]/[bold red]"
                    + str(player.battles_lost)
                    + " [white]([bold blue]"
                    + str(player.battles_played)
                    + "[white])"
                )
                if player.battle_streak > 1:
                    sleep(uniform(1, 2))
                    console.log(
                        "[bold white]Battle Win Streak: [bold green]"
                        + str(player.battle_streak)
                    )
                sleep(uniform(1, 2))
            except Exception:
                console.print_exception(show_locals=True)
                console.log(
                    "[bold white]Browser Status: [bold red]Error Occurred During Battle Process"
                )
                del page
                BROWSER["browser"].close()
                browser_status = False
            # Step 10: Sleep for set interval
            console.log(
                "[bold white]Rest Period: [bold hot_pink]"
                + str(BATTLE["battle_interval"])
                + " [bold white]Seconds"
            )
            print()

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
                p_browser = play.chromium.launch_persistent_context(
                    "./", headless=BROWSER["headless"], args=BROWSER["args"]
                )
                browser_status = True

                BROWSER["browser"] = p_browser
                BROWSER["creation"] = datetime.now()

                page = Page(console, BROWSER)
                sleep(uniform(1, 2))
    except KeyboardInterrupt:
        console.log("[bold red]Shutdown requested...")
        sleep(3)
    except:
        console.print_exception(show_locals=True)
    sys.exit()


if __name__ == "__main__":
    main()
