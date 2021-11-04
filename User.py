from datetime import datetime

import requests


class User:
    def __init__(self, username, email, password, request_quest):
        self.username = username
        self.email = email
        self.password = password
        self.request_quest = request_quest

        self.cards = self.get_cards()
        self.quest = self.get_quest()

        self.battles_played = 0
        self.battles_won = 0
        self.battle_streak = 0

        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Current Player: ' + username)
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +
              ' Current Deck Size: ' + str(len(self.cards)))
        print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + ' Current Quest: ' +
              str(self.quest['type']) + ' (' + str(self.quest['completed_total']) + '/' + str(self.quest['quest_total']) + ')')

    def get_cards(self):
        """ Get user's playable cards.
        """

        base_cards = [1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25, 26, 27, 28, 29, 30, 34, 35, 36, 37, 38, 39, 40, 41, 42, 45, 46, 47, 48, 49, 50, 51, 52, 60, 61, 62, 63, 64, 65, 66, 79, 157, 158, 159, 160, 161, 162,
                      163, 167, 168, 169, 170, 171, 172, 173, 174, 178, 179, 180, 181, 182, 183, 184, 185, 189, 140, 141, 145, 146, 147, 148, 149, 150, 151, 152, 156, 135, 136, 137, 138, 139, 140, 141, 145, 185, 189, 224, 190, 191, 192, 193, 194, 195, 196]
        p_cards = []

        try:
            player_cards_data = requests.get(
                'https://api2.splinterlands.com/cards/collection/' + self.username.lower()
            )
            player_cards = player_cards_data.json()['cards']

            for p_card in player_cards:
                # checks if base cards have been upgraded
                if p_card['card_detail_id'] in base_cards:
                    base_cards.remove(p_card['card_detail_id'])

                p_card_data = {}
                p_card_data['id'] = p_card['card_detail_id']
                p_card_data['level'] = p_card['level']
                p_cards.append(p_card_data)

            for base_card in base_cards:
                base_card_data = {}
                base_card_data['id'] = base_card
                base_card_data['level'] = 1
                p_cards.append(base_card_data)
            return p_cards
        except Exception as e:
            print(e)
            return base_cards

    def get_quest(self):
        """Get user's quest details.
        """

        possible_quests = {
            'Stir the Volcano': 'Fire',
            'Pirate Attacks': 'Water',
            'Lyanna\'s Call': 'Earth',
            'Defend the Borders': 'Life',
            'Rising Dead': 'Death',
            'Gloridax Revenge': 'Dragon',
            'Stubborn Mercenaries': 'Neutral',
            'Stealth Mission': 'Sneak',
            'High Priority Targets': 'Snipe'
        }

        try:
            player_quest_data = requests.get(
                'https://api.splinterlands.io/players/quests?username=' + self.username.lower()
            )
            player_quest = player_quest_data.json()[0]
            return {
                'type': possible_quests[player_quest['name']],
                'quest_total': player_quest['total_items'],
                'completed_total': player_quest['completed_items'],
                'claimed': player_quest['claim_date'],
            }
        except Exception as e:
            print(e)
            return None
