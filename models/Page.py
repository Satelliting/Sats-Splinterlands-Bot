from playwright.sync_api import sync_playwright
from time import sleep
from datetime import datetime


class Page:
    def __init__(self, browser, base_url):
        self.base_url = base_url
        self.creation_date = datetime.now()

        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Browser Launched')
        self.page = browser.new_page()

    def __del__(self):
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Browser Closed')

    def close_modal(self):
        """Attempts to close any modals open.
        """
        sleep(2)

        try:
            self.page.click('.modal-close-new', timeout=5000)
        except:
            pass

        try:
            self.page.click('.close', timeout=5000)
        except:
            pass

    def check_login_status(self):
        """Checks if user is currently logged in.

        Returns:
            [type]: True if logged in, False otherwise.
        """
        self.page.goto(self.base_url)
        sleep(3)
        try:
            self.page.wait_for_selector(
                '#log_in_button', state='visible', timeout=10000)
            return True
        except:
            return False

    def login(self, user):
        """Logs user into page.

        Args:
            user (User): Custom User Class

        Returns:
            bool: If login successful
        """
        self.page.wait_for_selector('#log_in_button > button', timeout=3000)
        self.page.click('#log_in_button > button')

        self.page.wait_for_selector('input#email', timeout=10000)
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Attempting Login')
        sleep(2)

        self.page.focus('input#email')
        self.page.type('input#email', user.email, delay=41)
        self.page.focus('input#password')
        self.page.type('input#password', user.password, delay=63)
        self.page.click('#login_dialog_v2 .btn-primary >> nth=1')
        sleep(5)

        # Ensures correct email/pass combination
        try:
            check = self.page.inner_text('#email ~ .help-block', timeout=10000)
        except:
            check = ''
            pass
        if len(check) > 0:
            return None

        print(datetime.now().strftime(
            "%m/%d/%Y, %H:%M:%S") + ' Status: Logged In')
        return True

    def calculate_ecr_wait(self, ecr_min, ecr_max):
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Calculating ECR')
        ecr_amount_percent = self.page.inner_text(
            '//*[@id="bs-example-navbar-collapse-1"]/ul[2]/li[2]/div[1]/div[3]/div[3]/div')
        ecr_amount = float(ecr_amount_percent.strip('%')) / 100

        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Current ECR: ' + str(ecr_amount_percent))

        if ecr_amount >= ecr_min:
            return 0

        wait_amount = 0.0
        while ecr_max > ecr_amount:
            ecr_max -= .001
            wait_amount += 1

        if wait_amount != 0.0:
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + ' Status: Waiting ' + str(wait_amount) +
                  ' Minutes ECR To Reach Minimum')
        return wait_amount * 60

    def battle_status(self):
        """Find if in team selection phase of battle.

        Returns:
            bool: If mid-battle, return False
        """
        self.page.goto(self.base_url + '/?p=battle_history')
        self.close_modal()
        sleep(3)
        try:
            self.page.wait_for_selector('.btn--create-team', timeout=3000)
            print(datetime.now().strftime(
                "%m/%d/%Y, %H:%M:%S") + ' Status: Mid-Battle')
            return False
        except:
            return True

    def initiate_battle(self):
        """Initiate Battle.
        """
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Initiating Battle')
        try:
            self.page.click('#battle_category_btn', timeout=5000)
            return True
        except Exception as e:
            print(e)
            return False

    def enter_card_selection(self):
        """Enter card selection screen.
        """
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Entering Card Selection Screen')
        self.page.click('.btn--create-team', timeout=250000)

    def get_battle_details(self):
        sleep(3)

        mana = int(self.page.inner_html('.mana-cap').strip())
        RULE_SET = self.page.query_selector_all(
            'div.combat__rules > div.row > div>  img')
        AVAIL_SPLINTERS = self.page.query_selector_all(
            'div.col-sm-4 > img')

        rule_set = ''
        for rule in RULE_SET:
            rule_set += rule.get_attribute(
                'data-original-title').split(':')[0] + '|'
        rule_set = rule_set[:-
                            1] if rule_set.endswith('|') else rule_set

        splinter_options = []
        for s_option in AVAIL_SPLINTERS:
            s_p = s_option.get_attribute(
                'data-original-title').split(':')
            if s_p[1].strip() == 'Active':
                splinter_options.append(s_p[0])

        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Battle Mana: ' + str(mana))
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Battle Rule Set: ' + str(rule_set))
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Battle Splinters: ' + str(splinter_options))

        return {
            'mana': mana,
            'rule_set': rule_set,
            'splinters': splinter_options
        }

    def click_cards(self, deck=None):
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Clicking Cards')
        # If no viable deck was found
        if deck == None:
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                  ' Status: No Deck Found, Clicking First Summoner, First Monster')
            # first summoner select
            summoner_id = 0
            while True:
                try:
                    if summoner_id > 999:
                        break
                    self.page.click(
                        'div[card_detail_id="' + str(summoner_id) + '"]', timeout=300)
                    break
                except:
                    summoner_id += 1
            sleep(2)
            # if summoner selected was Dragon
            try:
                self.page.click(
                    'label[id^="filter-element-"]', timeout=5000)
            except:
                pass
            # first monster select
            monster_id = 0
            while True:
                try:
                    if monster_id > 999:
                        break
                    self.page.click(
                        'div[card_detail_id="' + str(monster_id) + '"]', timeout=300)
                    break
                except:
                    monster_id += 1
            return True
        else:
            self.page.click(
                'div[card_detail_id="' + str(deck['summoner']['id']) + '"]')

            if deck['summoner']['splinter'] == 'Dragon':
                deck_splinter = deck['monsters'][0]['splinter']
                self.page.click(
                    '#filter-element-' + deck_splinter.lower() + '-button ~ label', timeout=5000)

            for card in deck['monsters']:
                self.page.click(
                    'div[card_detail_id="' + str(card['id']) + '"]')
                sleep(0.5)
            return True

    def start_battle(self):
        """Start the battle and wait for the opponent.

        Returns:
            bool: True if battle was fought.
        """
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Waiting For Opponent')
        self.page.click('.btn-green')
        try:
            self.page.wait_for_selector('#btnRumble', timeout=300000)
        except:
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                  ' Status: Opponent Surrendered')
            return False

        try:
            print(datetime.now().strftime(
                "%m/%d/%Y, %H:%M:%S") + ' Status: Battling')
            self.page.click('#btnRumble')
            self.page.click('#btnSkip')
        except:
            return False

        return True

    def check_winner(self):
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Checking Winner')
        try:
            winner = self.page.inner_text(
                '.player.winner .bio__name__display', timeout=10000).lower()
            self.page.click('.btn.btn--done', timeout=10000)

            print(datetime.now().strftime(
                "%m/%d/%Y, %H:%M:%S") + ' Winner: ' + winner)
            return winner
        except:
            print(datetime.now().strftime(
                "%m/%d/%Y, %H:%M:%S") + ' Winner: Tied')
            return 'tied'

    def claim_reward(self, reward_type):
        try:
            self.page.goto(self.base_url + '/?p=battle_history')
            self.close_modal()
            sleep(2)
            if reward_type == 'season':
                self.page.click('#claim-btn.reward_claim_btn',
                                state='visible', timeout=10000)
                print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                      ' Status Season Reward Claimed')
                self.page.wait_for_selector(
                    '#open_pack_dialog', state='visible')
                return True
            elif reward_type == 'quest':
                self.page.click(
                    '#quest_claim_btn.reward_claim_btn.quest_info_one', state='visible', timeout=10000)
                print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                      ' Status Quest Reward Claimed')
                self.page.wait_for_selector(
                    '#open_pack_dialog', state='visible')
                return True
            else:
                return None
        except:
            return None
