from datetime import datetime
from random import randint
from time import sleep

import requests


class Battle:
    def __init__(self, console, player, cards_details, battle_details, battlebase):
        self.console = console

        self.player = player
        self.cards_details = cards_details
        self.battlebase = battlebase

        self.mana = battle_details["mana"] or 99
        self.rule_set = battle_details["rule_set"] or "Standard"
        self.splinters = battle_details["splinters"] or [
            "Fire",
            "Water",
            "Earth",
            "Light",
            "Death",
            "Dragon",
        ]

    def get_deck(self, prioritize_quest):
        """Gets deck for player.

        Returns:
            object: deck from battlebase
        """

        battle_splinters = self.splinters

        def filter_deck(battle):
            if (
                battle["md"]["mana"] <= self.mana
                and battle["md"]["rule_set"] == self.rule_set
                and battle["team"]["summoner"]["splinter"] in battle_splinters
            ):
                return True
            else:
                return False

        if (
            self.player.quest != None
            and self.player.quest["completed_total"] < self.player.quest["quest_total"]
            and prioritize_quest
        ):
            # Not Currently Supported Quests
            if self.player.quest["type"] not in ["Sneak", "Snipe", "Neutral"]:
                self.console.log("[bold red]Prioritizing Quest Deck")
                sleep(randint(1, 2))
                battle_splinters = [self.player.quest["type"]]

        db_decks = list(filter(filter_deck, self.battlebase))

        if len(db_decks) == 0:
            self.console.log("[bold red]Cannot prioritize quest")
            sleep(randint(1, 2))
            battle_splinters = self.splinters
            db_decks = list(filter(filter_deck, self.battlebase))
        else:
            battle_splinters = [self.player.quest["type"]]

        self.console.log(
            "[bold white]Mana/Rule Set/Splinter Matching Decks: [bold yellow]"
            + str(len(db_decks))
        )
        sleep(1)

        possible_decks = []
        for battle in db_decks:
            viable = False

            player_summoner = [
                card
                for card in self.player.cards
                if card.get("id") == battle["team"]["summoner"]["id"]
            ]
            # checks if player has card with battle summoner card_detail_id
            if len(player_summoner) == 0:
                viable = False
            else:
                for battle_monster in battle["team"]["monsters"]:
                    player_monster = [
                        card
                        for card in self.player.cards
                        if card.get("id") == battle_monster["id"]
                    ]
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

        self.console.log(
            "[bold white]Card Matching Decks: [bold yellow]" + str(len(db_decks))
        )
        sleep(1)

        chosen_deck = None
        chosen_deck_occurrence = 0
        chosen_deck_mana = 0

        if len(possible_decks) > 0:
            for deck in possible_decks:
                # Check if Dragon deck sub-splinter is available
                if deck["team"]["summoner"]["splinter"] == "Dragon":
                    if deck["team"]["monsters"][0]["splinter"] not in battle_splinters:
                        continue
                if deck["md"]["mana"] > chosen_deck_mana:
                    # Checks if battle deck with one less mana has more wins
                    if deck["md"]["mana"] == chosen_deck_mana + 1:
                        if deck["md"]["amount"] > chosen_deck_occurrence:
                            chosen_deck = deck["team"]
                            chosen_deck_occurrence = deck["md"]["amount"]
                            chosen_deck_mana = deck["md"]["mana"]
                    else:
                        chosen_deck = deck["team"]
                        chosen_deck_occurrence = deck["md"]["amount"]
                        chosen_deck_mana = deck["md"]["mana"]
                elif deck["md"]["mana"] == chosen_deck_mana:
                    if deck["md"]["amount"] > chosen_deck_occurrence:
                        chosen_deck = deck["team"]
                        chosen_deck_occurrence = deck["md"]["amount"]
                        chosen_deck_mana = deck["md"]["mana"]
        else:
            chosen_deck = None

        emoji_splinters = [
            "Fire :fire:",
            "Water :water_wave:",
            "Earth :leaves:",
            "Light :light_bulb:",
            "Death :skull:",
            "Dragon :dragon:",
        ]

        emoji_splinter_match = [
            match
            for match in emoji_splinters
            if chosen_deck["summoner"]["splinter"] in match
        ]

        if chosen_deck != None:
            self.console.log(
                "[bold white]Chosen Deck: [bold yellow3]"
                + (emoji_splinter_match[0] or chosen_deck["summoner"]["splinter"])
                + " [bold white]([bold cyan]"
                + str(chosen_deck_mana)
                + "[bold white])"
            )
            sleep(1)
            self.console.log(
                "[bold white]Deck Win Count: [bold green]" + str(chosen_deck_occurrence)
            )
            sleep(1)
            self.console.log(
                "[bold white]Summoner: [bold yellow3]"
                + self.cards_details[chosen_deck["summoner"]["id"] - 1]["name"]
                + " [bold white]([bold hot_pink]"
                + str(chosen_deck["summoner"]["id"])
                + "[bold white])"
            )
            sleep(1)
            for order, monster in enumerate(chosen_deck["monsters"]):
                self.console.log(
                    "[bold white]Monster #"
                    + str(order + 1)
                    + ": [bold yellow3]"
                    + self.cards_details[chosen_deck["monsters"][order]["id"] - 1][
                        "name"
                    ]
                    + " [bold white]([bold hot_pink]"
                    + str(chosen_deck["monsters"][order]["id"])
                    + "[bold white])"
                )
                sleep(1)

        return chosen_deck

    def check_winner(self):
        """Checks who the winner of the match was.

        Returns:
            String: Username of winner.
        """

        with self.console.status("[bold blue]Checking Winner...") as status:
            sleep(randint(1, 3))

            player_battle_data = requests.get(
                "https://api2.splinterlands.com/battle/history?player="
                + self.player.username.lower()
            )
            player_battle = player_battle_data.json()["battles"][0]
            winner = player_battle["winner"]

        return winner
