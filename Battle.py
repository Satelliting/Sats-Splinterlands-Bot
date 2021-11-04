from datetime import datetime
from time import sleep

import requests


class Battle:
    def __init__(self, user, cards_details, battle_details, battlebase):
        self.user = user
        self.cards_details = cards_details
        self.battlebase = battlebase

        self.mana = battle_details['mana'] or 99
        self.rule_set = battle_details['rule_set'] or 'Standard'
        self.splinters = battle_details['splinters'] or [
            'Fire', 'Water', 'Earth', 'Light', 'Death']

    def get_deck(self):
        """Gets deck for user.

        Returns:
            object: deck from battlebase
        """
        print(datetime.now().strftime(
            "%m/%d/%Y, %H:%M:%S") + ' Status: Getting Deck')
        battle_splinters = self.splinters

        def filter_deck(battle):
            if battle['md']['mana'] <= self.mana and battle['md']['rule_set'] == self.rule_set and battle['team']['summoner']['splinter'] in battle_splinters:
                return True
            else:
                return False

        if self.user.quest != None and self.user.quest['completed_total'] < self.user.quest['quest_total'] and self.user.request_quest:
            # Not Currently Supported Quests
            if self.user.quest['type'] not in ['Sneak', 'Snipe', 'Neutral']:
                print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                      ' Status: Prioritizing Quest')
                battle_splinters = [self.user.quest['type']]

        db_decks = list(filter(filter_deck, self.battlebase))

        if len(db_decks) == 0:
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                  ' Status: Cannot Prioritize Quest')
            battle_splinters = self.splinters
            db_decks = list(filter(filter_deck, self.battlebase))
        else:
            battle_splinters = [self.user.quest['type']]

        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Mana/Rule Set/Splinter Matching Decks: ' + str(len(db_decks)))

        possible_decks = []
        for battle in db_decks:
            viable = False

            player_summoner = [card for card in self.user.cards if card.get(
                'id') == battle['team']['summoner']['id']]
            # checks if player has card with battle summoner card_detail_id
            if len(player_summoner) == 0:
                viable = False
            else:
                for battle_monster in battle['team']['monsters']:
                    player_monster = [card for card in self.user.cards if card.get(
                        'id') == battle_monster['id']]
                    # checks if player has card with battle monster card_detail_id
                    if len(player_monster) > 0:
                        viable = True
                        # assigns player card to first instance returned from cards
                        # player_monster = player_monster[0]
                        # checks if levels match
                        # if battle_monster['level'] == player_monster['level']:
                        #     viable = True
                        # else:
                        #     viable = False
                        #     break
                    else:
                        viable = False
                        break
            if viable:
                possible_decks.append(battle)

        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Card Matching Decks: ' + str(len(possible_decks)))
        chosen_deck = None
        chosen_deck_occurrence = 0
        chosen_deck_mana = 0

        if len(possible_decks) > 0:
            for deck in possible_decks:
                # Check if Dragon deck sub-splinter is available
                if deck['team']['summoner']['splinter'] == 'Dragon':
                    if deck['team']['monsters'][0]['splinter'] not in battle_splinters:
                        continue
                if deck['md']['mana'] > chosen_deck_mana:
                    # Checks if battle deck with one less mana has more wins
                    if deck['md']['mana'] == chosen_deck_mana + 1:
                        if deck['md']['amount'] > chosen_deck_occurrence:
                            chosen_deck = deck['team']
                            chosen_deck_occurrence = deck['md']['amount']
                            chosen_deck_mana = deck['md']['mana']
                    else:
                        chosen_deck = deck['team']
                        chosen_deck_occurrence = deck['md']['amount']
                        chosen_deck_mana = deck['md']['mana']
                elif deck['md']['mana'] == chosen_deck_mana:
                    if deck['md']['amount'] > chosen_deck_occurrence:
                        chosen_deck = deck['team']
                        chosen_deck_occurrence = deck['md']['amount']
                        chosen_deck_mana = deck['md']['mana']
        else:
            chosen_deck = None

        if chosen_deck != None:
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + ' Chosen Deck: ' +
                  chosen_deck['summoner']['splinter'] + " (" + str(chosen_deck_mana) + ")")
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
                  ' Deck Win Count: ' + str(chosen_deck_occurrence))
            print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + ' Summoner: ' +
                  self.cards_details[chosen_deck['summoner']['id'] - 1]['name'] + ' (' + str(chosen_deck['summoner']['id']) + ')')
            for order, monster in enumerate(chosen_deck['monsters']):
                print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + ' Monster #' + str(order+1) + ': ' +
                      self.cards_details[chosen_deck['monsters'][order]['id'] - 1]['name'] + ' (' + str(chosen_deck['monsters'][order]['id']) + ')')

        return chosen_deck

    def check_winner(self):
        """Checks who the winner of the match was.

        Returns:
            String: Username of winner.
        """
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Status: Checking Winner')
        sleep(3)

        player_battle_data = requests.get(
            'https://api2.splinterlands.com/battle/history?player=' + self.user.username.lower()
        )
        player_battle = player_battle_data.json()['battles'][0]
        winner = player_battle['winner']

        print(datetime.now().strftime(
            "%m/%d/%Y, %H:%M:%S") + ' Winner: ' + winner)
        return winner
