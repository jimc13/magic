#!/usr/bin/python3
assert False, "This is depricated by count_cards_from_spreadsheet.py"
import re
import operator
from parse_deck_to_objects import get_untap_card
cards = {}
exceptions = set()
with open("uol_decks.txt") as f:
    for line in f:
        line = line.strip()
        line = line.strip('"')
        if not line or "//sideboard" in line or "//deck" in line or line == "SB" or "Sideboard" in line or "Decklist" in line:
            continue
        try:
            num, name = re.match(r"""(\d+)x? ([^()\n]*).*""", line).groups()
        except Exception as e:
            exceptions.add(line)
            continue

        name = name.strip()
        name = name.strip("\"")
        name = name.strip()
        if name not in cards:
            c = get_untap_card('0 {}'.format(name))
            name = c[1].name
            cards[name] = 0

        cards[name] += int(num)

    sorted_cards = sorted(cards.items(), key=operator.itemgetter(1), reverse=True)
    for card in sorted_cards:
        print('{} {}'.format(card[0], card[1]))

    if exceptions:
        print("\n*****Errors:****\n {}".format(exceptions))
