#!/usr/bin/env python3
import re
import pickle
from mtgsdk import Card
import logging
import logging.handlers

# cd C:\Users\jimac\Documents\Dev\Python\Magic
# venv\Scripts\activate
# python parse_deck.py

class Decklist(list):
    """
    List to be used to store objects that have attribute name that should be
    printed instead of a representaion of the object
    """
    def __str__(self):
        cards = []
        for card in self:
            cards.append(card.name)

        return "\n".join(cards)

class Deck():
    def __init__(self):
        self.mainboard = Decklist()
        self.sideboard = Decklist()
        self.deck = Decklist()

    def _untap_parser(self):
        """
        Parse a decklist exported from untap.  Currently not designed for
        commander - it assumes there is only a mainboard and a sideboard.
        """


        decklist = self.decklist[self.decklist.index("//deck-1")+1:]
        sideboard = []
        if "//sideboard-1" in decklist:
            sideboard_position = decklist.index("//sideboard-1")
            sideboard = decklist[sideboard_position+1:]
            decklist = decklist[:sideboard_position]

        for line in decklist:
            if not line:
                continue
            quantity, card = get_untap_card(line)
            self.mainboard += [card] * quantity

        for line in sideboard:
            if not line:
                continue
            quantity, card = get_untap_card(line)
            self.sideboard += [card] * quantity

    def _parse_deck(self):
        """
        Check the format of the decklist and pass it through to the correct
        parser method
        """
        Deck._untap_parser(self)

    def parse_decklist(self, decklist):
        """
        Input decklist as a file or list
        """
        if isinstance(decklist, str):
            # If the file doesn't exist I'm happy to have that be a fatal error
            with open(decklist) as f:
                decklist = list(map(str.strip, f.readlines()))

        assert isinstance(decklist, list)
        self.decklist = decklist
        Deck._parse_deck(self)


#def read_untap_file(untap_file):
#    with open(untap_file) as f:
#        for line in f:

#https://docs.python.org/2/library/random.html#random.shuffle
#https://www.reddit.com/r/codereview/comments/3h2vdh/python_magic_the_gathering_deck_brute_force/
#https://codereview.stackexchange.com/questions/85751/implement-blackjack-in-python-with-oop
#https://stackoverflow.com/questions/12044970/not-list-inherited-deck-class-card-games-can-be-used-in-for-loops-without

#https://github.com/MagicTheGathering/mtg-sdk-python

def get_untap_card(line):
    quantity, cardname = line.split(' ', 1)
    cardnames = None
    if " // " in cardname:
        cardnames = cardname.split(" // ")
        cardname = cardnames[0]

    matches = Card.where(name=cardname).all()
    assert matches, "No cards found matching {}".format(cardname)
    exact_matches = []
    for card in matches:
        # More fussy matching that just causes issues when using dirty imput
        # data
        #if card.name == cardname and card.names == cardnames:
        if card.name == cardname:
            exact_matches.append(card)

    assert exact_matches, "No exact matches found for {}".format(cardname)
    return quantity, exact_matches[0]

def count_sources(deck):
    lands = []
    colours = {"W": 0, "U": 0, "B": 0, "R": 0,"G": 0, "C": 0}
    for card in deck.mainboard:
        if "Land" in card.type:
            lands.append(card)

    for land in lands:
        for colour in land.color_identity:
            colours[colour] += 1
        #print(land.name, land.text)
        #list_of_segments_with_colours_in = re.findall(r"""{T}: Add (.*) to your mana pool.""", land.text)
        #assert list_of_segments_with_colours_in, "Land '{}' was in an unexpected format:\n{}".format(land.name, land.text)
        #for segments_with_colours_in in list_of_segments_with_colours_in:
        #    found_colours = re.findall("{.}", segments_with_colours_in)
        #    assert found_colours, "Land '{}' was in an unexpected format:\n{}".format(land.name, land.text)
        #    for colour in found_colours:
        #        colours[colour[1]] += 1

    return colours

# Currently bugged
def get_requirements(deck):
    logger = logging.getLogger(__name__)
    colours = ["W", "U", "B", "R", "G", "C"]
    turns = {}
    for card in deck.mainboard:
        turn = str(card.cmc)
        mana = card.mana_cost
        card_mana_cost = {}
        while mana:
            colour, mana = mana[1], mana[3:]
            if colour.isdigit():
                continue

            if colour in colours:
                card_mana_cost[colour] = card_mana_cost.get(colour, 0) + 1

        turns[turn] = turns.get(turn, []) + [card_mana_cost]

    for turn in sorted(turns):
        for coloured_mana_cost_of_card in turns[turn]:
            logger.info("Turn: {} Coloured Mana Cost: {}".format(turn, coloured_mana_cost_of_card))

def main():
    # This has some unrelated log testing
    logfile = "log.txt"
    logger = logging.getLogger(__name__)
    log_handler = logging.handlers.WatchedFileHandler(logfile)
    formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s', '%d-%m-%Y %H:%M:%S')
    log_handler.setFormatter(formatter)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)

    decklist = "decks/Gruul-legal.untap.txt"
    pickle_file = "decks/{}.pickle".format(decklist)
    try:
        with open(pickle_file, "rb") as f:
            deck = pickle.load(f)

    except FileNotFoundError as e:
        deck = Deck()
        deck.parse_decklist(decklist)
        with open(pickle_file, "wb") as f:
            pickle.dump(deck, f)

    logger.info("MB:")
    logger.info(deck.mainboard)
    logger.info("SB:")
    logger.info(deck.sideboard)
    logger.info(count_sources(deck))
    get_requirements(deck)

    import test_other
    test_other.cats()
    logger.error("cats will be logged again")
    from test_other import cats
    cats()
    logger.error("test")

if __name__ == "__main__":
    main()
