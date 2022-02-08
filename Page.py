from playwright.sync_api import sync_playwright
from time import sleep
from datetime import datetime
from random import randint, uniform

import sys


class Page:
    def __init__(self, console, browser_details):
        self.console = console

        self.browser = browser_details["browser"]
        self.base_url = browser_details["base_url"]

        console.log("[bold magenta]Browser Launched")
        self.page = self.browser.new_page()
        self.page.goto(self.base_url)
        self.page.wait_for_load_state()

    def __del__(self):
        self.console.log("[bold magenta]Browser Closed")

    def close_modal(self):
        """Attempts to close any modals open."""

        try:
            self.page.click(".modal-close-new", timeout=2000)
        except:
            pass

        try:
            self.page.click(".close", timeout=2000)
        except:
            pass

    def logout_account(self):
        try:
            self.page.evaluate("() => SM.Logout();")
        except:
            pass

    def is_logged_in(self, username):
        """Checks if user is currently logged in.

        Returns:
            [type]: True if logged in, False otherwise.
        """

        self.page.wait_for_load_state()

        try:
            self.page.wait_for_selector(".bio__avatar", state="visible", timeout=5000)
            return username == self.page.inner_text(".bio__name__display").lower()
        except:
            return False

    def login(self, user):
        """Logs user into page.

        Args:
            user (User): Custom User Class

        Returns:
            bool: If login successful
        """

        # waits for page load
        self.page.goto(self.base_url)
        self.page.wait_for_load_state()

        # clicks login button to open modal
        self.console.log("[bold magenta]Opening login modal")
        self.page.click("#log_in_button > button")
        sleep(randint(2, 4))

        # wait for modal to finish loading
        self.page.wait_for_selector("input#email", timeout=10000)
        sleep(randint(2, 4))  # utilized to wait for animation to finish

        # enter login details
        self.console.log("[bold magenta]Entering credentials")
        self.page.focus("input#email")
        self.page.type("input#email", user.email, delay=randint(35, 80))
        self.page.focus("input#password")
        self.page.type("input#password", user.password, delay=randint(40, 90))

        # click login button
        self.console.log("[bold magenta]Clicking login button")
        self.page.click("#login_dialog_v2 .btn-primary >> nth=1")
        sleep(randint(3, 5))

        # ensures correct email/password combination
        check = ""
        try:
            check = self.page.inner_text("#email ~ .help-block", timeout=5000)
        except:
            check = ""

        if len(check) > 0:
            return None
        else:
            return True

    def calculate_ecr_wait(self, ecr_min, ecr_max):
        """Calculate ECR wait time needed."""
        ecr_amount_percent = self.page.inner_text(
            ".dec-options div:nth-child(3) div:nth-child(1)"
        )
        ecr_amount = float(ecr_amount_percent.strip("%")) / 100

        self.console.log("[bold magenta]Current ECR: " + str(ecr_amount_percent))

        if ecr_amount >= ecr_min:
            return 0

        wait_amount = 0.0
        while ecr_max > ecr_amount:
            ecr_max -= 0.01
            wait_amount += 1

        return wait_amount * 60 * 60

    def is_mid_battle(self):
        """Find if in team selection phase of battle.

        Returns:
            bool: If mid-battle, return True
        """

        self.page.goto(self.base_url + "/?p=battle_history")
        try:
            self.page.wait_for_selector(".btn--create-team", timeout=3000)
            return True
        except:
            return False

    def initiate_battle(self):
        """Initiate Battle."""

        try:
            self.page.click("#battle_category_btn", timeout=5000)
            sleep(randint(2, 4))
            self.page.click(".btn--create-team", timeout=250000)
            return True
        except:
            return False

    def get_battle_details(self):
        try:
            mana = int(self.page.inner_html(".mana-cap").strip())
            page_rule_set = self.page.query_selector_all(
                "div.combat__rules > div.row > div>  img"
            )
            available_splinters = self.page.query_selector_all("div.col-sm-4 > img")

            rule_set = ""
            for rule in page_rule_set:
                rule_set += (
                    rule.get_attribute("data-original-title").split(":")[0] + "|"
                )
            rule_set = rule_set[:-1] if rule_set.endswith("|") else rule_set

            splinter_options = []
            for s_option in available_splinters:
                s_p = s_option.get_attribute("data-original-title").split(":")
                if s_p[1].strip() == "Active":
                    splinter_options.append(s_p[0])

            self.console.log("[bold yellow]Battle Mana: " + str(mana))
            sleep(1)
            self.console.log("[bold yellow]Battle Rule Set: " + str(rule_set))
            sleep(1)
            self.console.log("[bold yellow]Battle Splinters: " + str(splinter_options))
            sleep(1)

            return {"mana": mana, "rule_set": rule_set, "splinters": splinter_options}
        except:
            self.console.print_exception(show_locals=True)
            sys.exit()

    def click_cards(self, deck=None):
        with self.console.status("[bold white]Clicking Cards", spinner="arc") as status:
            sleep(randint(2, 3))

            # If no viable deck was found
            if deck == None:
                self.console.log(
                    "[bold orange3]No Deck Found, Clicking First Summoner, First Monster"
                )
                # first summoner select
                summoner_id = 0
                while True:
                    try:
                        if summoner_id > 999:
                            break
                        self.page.click(
                            'div[card_detail_id="' + str(summoner_id) + '"]',
                            timeout=300,
                        )
                        break
                    except:
                        summoner_id += 1
                sleep(randint(1, 2))
                # if summoner selected was Dragon
                try:
                    self.page.click('label[id^="filter-element-"]', timeout=5000)
                except:
                    pass
                # first monster select
                monster_id = 0
                while True:
                    try:
                        if monster_id > 999:
                            break
                        self.page.click(
                            'div[card_detail_id="' + str(monster_id) + '"]', timeout=300
                        )
                        break
                    except:
                        monster_id += 1
                return True
            else:
                self.page.click(
                    'div[card_detail_id="' + str(deck["summoner"]["id"]) + '"]'
                )

                if deck["summoner"]["splinter"] == "Dragon":
                    deck_splinter = deck["monsters"][0]["splinter"]
                    self.page.click(
                        "#filter-element-" + deck_splinter.lower() + "-button ~ label",
                        timeout=5000,
                    )

                for card in deck["monsters"]:
                    self.page.click('div[card_detail_id="' + str(card["id"]) + '"]')
                    sleep(uniform(0, 1))
                return True

    def start_battle(self):
        """Start the battle and wait for the opponent.

        Returns:
            bool: True if battle was fought.
        """

        with self.console.status("[bold yellow]Waiting For Opponent") as status:
            sleep(randint(2, 3))
            self.page.click(".btn-green")

            try:
                self.page.wait_for_selector("#btnRumble", timeout=300000)
            except:
                self.console.log("[bold green]Opponent Surrendered")
                return False
            return True

    def claim_reward(self, reward_type):
        try:
            self.page.goto(self.base_url + "/?p=battle_history")
            self.close_modal()
            sleep(3)

            if reward_type == "season":
                self.page.click("#reward_claim_container > #claim-btn", timeout=10000)
                print(
                    datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                    + " Status Season Reward Claimed"
                )
                self.page.wait_for_selector("#open_pack_dialog", state="visible")
                return True
            elif reward_type == "quest":
                self.page.click(
                    "#quest_claim_container > #quest_claim_btn", timeout=10000
                )
                print(
                    datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                    + " Status Quest Reward Claimed"
                )
                self.page.wait_for_selector("#open_pack_dialog", state="visible")
                return True
            else:
                return None
        except:
            return None
