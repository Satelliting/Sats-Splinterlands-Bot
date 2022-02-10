from datetime import datetime
from time import sleep
from random import randint

import requests


class User:
    def __init__(self, console, user_details):
        self.console = console

        self.username = user_details["username"]
        self.email = user_details["email"]
        self.password = user_details["password"]

        self.cards = self.get_cards()
        self.quest = self.get_quest()

        self.battles_played = 0
        self.battles_won = 0
        self.battles_drawn = 0
        self.battles_lost = 0
        self.battle_streak = 0

        self.console.log("[bold white]Current Player: [bold blue]" + self.username)
        sleep(1)
        self.console.log(
            "[bold white]Player's Deck Size: [bold blue]" + str(len(self.cards))
        )
        sleep(1)
        self.console.log(
            "[bold white]Player's Quest: [bold blue]"
            + str(self.quest["type"])
            + " [bold white]([bold green]"
            + str(self.quest["completed_total"])
            + "[bold white]/[bold yellow]"
            + str(self.quest["quest_total"])
            + "[bold white])"
        )

    def get_cards(self):
        """Get user's playable cards."""

        base_cards = [
            157,
            158,
            159,
            160,
            395,
            396,
            397,
            398,
            399,
            161,
            162,
            163,
            167,
            400,
            401,
            402,
            403,
            440,
            168,
            169,
            170,
            171,
            381,
            382,
            383,
            384,
            385,
            172,
            173,
            174,
            178,
            386,
            387,
            388,
            389,
            437,
            179,
            180,
            181,
            182,
            334,
            367,
            368,
            369,
            370,
            371,
            183,
            184,
            185,
            189,
            372,
            373,
            374,
            375,
            439,
            146,
            147,
            148,
            149,
            409,
            410,
            411,
            412,
            413,
            150,
            151,
            152,
            156,
            414,
            415,
            416,
            417,
            135,
            135,
            136,
            137,
            138,
            353,
            354,
            355,
            356,
            357,
            139,
            140,
            141,
            145,
            358,
            359,
            360,
            361,
            438,
            224,
            190,
            191,
            192,
            157,
            423,
            424,
            425,
            426,
            194,
            195,
            196,
            427,
            428,
            429,
            441,
        ]
        p_cards = []

        try:
            player_cards_data = requests.get(
                "https://api2.splinterlands.com/cards/collection/"
                + self.username.lower()
            )
            player_cards = player_cards_data.json()["cards"]

            for p_card in player_cards:
                # checks if base cards have been upgraded
                if p_card["card_detail_id"] in base_cards:
                    base_cards.remove(p_card["card_detail_id"])

                p_card_data = {}
                p_card_data["id"] = p_card["card_detail_id"]
                p_card_data["level"] = p_card["level"]
                p_cards.append(p_card_data)

            for base_card in base_cards:
                base_card_data = {}
                base_card_data["id"] = base_card
                base_card_data["level"] = 1
                p_cards.append(base_card_data)
            return p_cards
        except Exception:
            self.console.print_exception(show_locals=True)
            return base_cards

    def get_quest(self):
        """Get user's quest details."""

        possible_quests = {
            "Stir the Volcano": "Fire",
            "Pirate Attacks": "Water",
            "Lyanna's Call": "Earth",
            "Defend the Borders": "Life",
            "Rising Dead": "Death",
            "Gloridax Revenge": "Dragon",
            "Stubborn Mercenaries": "Neutral",
            "Stealth Mission": "Sneak",
            "High Priority Targets": "Snipe",
        }

        try:
            player_quest_data = requests.get(
                "https://api.splinterlands.io/players/quests?username="
                + self.username.lower()
            )
            player_quest = player_quest_data.json()[0]
            return {
                "type": possible_quests[player_quest["name"]],
                "quest_total": player_quest["total_items"],
                "completed_total": player_quest["completed_items"],
                "claimed": player_quest["claim_date"],
            }
        except Exception:
            self.console.print_exception(show_locals=True)
            return None
