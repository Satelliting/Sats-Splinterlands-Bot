from models.User import User
from models.Battle import Battle
from models.Page import Page

from dotenv import load_dotenv
from time import sleep
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

import os
import sys
import json
import requests


# load .env variables
load_dotenv(override=True)

# gets global user details
USERNAME = os.getenv('USERNAME')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

# get global browser details
HEADLESS = os.getenv('HEADLESS').lower() == 'true'
BATTLE_INTERVAL = int(os.getenv('BATTLE_INTERVAL'))
ECR_MIN = float(int(os.getenv('ECR_MIN')) / 100)
ECR_MAX = float(int(os.getenv('ECR_MAX')) / 100)
BASE_URL = 'https://splinterlands.com'

# gets misc details
CARDS_DETAILS = json.loads(requests.get(
    'https://api.splinterlands.io/cards/get_details').content)
PRIORITIZE_QUEST = os.getenv('PRIORITIZE_QUEST').lower() == 'true'
CLAIM_REWARD_QUEST = os.getenv('CLAIM_REWARD_QUEST').lower() == 'true'
CLAIM_REWARD_SEASON = os.getenv('CLAIM_REWARD_SEASON').lower() == 'true'

# Checks if console arguments passed (override .env)
if len(sys.argv) > 4:
    USERNAME = sys.argv[1]
    EMAIL = sys.argv[2]
    PASSWORD = sys.argv[3]


def main():
    # Step 0: Build Page
    play = sync_playwright().start()
    browser = play.chromium.launch(
        headless=HEADLESS,
        args=['--no-sandbox',
              '--disable-setuid-sandbox',
              '--single-process',
              '--hide-scrollbars',
              '--mute-audio',
              '--disable-web-security'
              ]
    )
    page = Page(browser, BASE_URL)

    BATTLES_PLAYED = 0
    BATTLES_WON = 0

    browser_life = datetime.now()
    browser_status = True
    browser_life_allowed = 20
    while True:
        try:
            # Step 1: Setup Player
            player = User(USERNAME, EMAIL, PASSWORD, PRIORITIZE_QUEST)
            # Step 2: Attempt to login player (If fails, already logged in)
            try:
                page.login(player)
            except:
                pass
            # Step 3: Check if player is already in battle
            if page.battle_status():
                # Step 3.1: Calculate how long we should wait for ECR to reset
                ecr_wait = page.calculate_ecr_wait(ECR_MIN, ECR_MAX)
                # Step 3.2: If have to wait, close browser and user data
                if ecr_wait > 0:
                    browser.close()
                    sleep(ecr_wait)
                    browser = play.chromium.launch(
                        headless=HEADLESS,
                        args=['--no-sandbox',
                              '--disable-setuid-sandbox',
                              '--single-process',
                              '--hide-scrollbars',
                              '--mute-audio',
                              '--disable-web-security'
                              ]
                    )
                    page = Page(BASE_URL, HEADLESS)
                    continue
                # Step 3.2.1: If no wait, initiate battle
                else:
                    page.initiate_battle()
            else:
                ecr_wait = 0
            # Step 4: Enter the card selection screen
            page.enter_card_selection()
            # Step 4.1 Create battle instance with battle details
            battle_details = page.get_battle_details()
            battle = Battle(player, CARDS_DETAILS, battle_details)
            # Step 5: Choose deck from battle deck logs
            deck = battle.get_deck()
            # Step 6: Click cards on the page
            page.click_cards(deck)
            # Step 7: Start the battle on the page
            page.start_battle()
            # Step 8: Check who won the battle
            winner = page.check_winner()
            if winner == USERNAME:
                BATTLES_WON += 1
            BATTLES_PLAYED += 1
            # Step 9: Attempts to claim rewards
            if CLAIM_REWARD_QUEST:
                page.claim_reward('quest')
            if CLAIM_REWARD_SEASON:
                page.claim_reward('season')

            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                  ' Battles Played: ' + str(BATTLES_PLAYED))
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                  ' Battles Won: ' + str(BATTLES_WON))
        except Exception as e:
            print(e)
            print('\n\n' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                  ' Status: Error Occurred During Battle Process')
            browser.close()
            browser_status = False
        # Step 10: Sleep for set interval
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Resting: ' + str(BATTLE_INTERVAL) + ' Seconds')
        # Step 10.1: Closer browser if older than browser_life_allowed  minutes or was closed
        if browser_life < datetime.now() - timedelta(minutes=browser_life_allowed) and browser_status != False:
            browser.close()
            browser_status = False
        sleep(BATTLE_INTERVAL)
        # Step 10.2: Open browser if old one was closed
        if browser_status == False:
            browser_life = datetime.now()
            browser_status = True
            browser = play.chromium.launch(
                headless=HEADLESS,
                args=['--no-sandbox',
                      '--disable-setuid-sandbox',
                      '--single-process',
                      '--hide-scrollbars',
                      '--mute-audio',
                      '--disable-web-security'
                      ]
            )
            page = Page(browser, BASE_URL)


if __name__ == '__main__':
    while True:
        main()
