import requests
import re
import operator
from parse_deck_to_objects import get_untap_card

def get_list_from_goldfish(url):
    goldfish_id = re.search(r"""mtggoldfish.com/deck/(\d+)""", url).group(1)
    r = requests.get("https://www.mtggoldfish.com/deck/download/{}".format(goldfish_id))
    main, side = r.text.replace('\r\n', '\n').split('\n\n')
    return main.split('\n'), side.split('\n')

def add_card_to_cards(card, cards):
    # I have group to allow people to prefix their cards
    # Not matching parentheses to drop set ids exported by untap
    num, name = re.match(r"""(?:i have )?(?:SB:  ?)?(\d+)x?[ \t]([^()\n]*).*""", card).groups()
    name = name.strip()
    name = name.strip("\"")
    name = name.strip()
    name = name.lower()
    if name not in cards:
        #c = get_untap_card('0 {}'.format(name))
        #name = c[1].name
        cards[name] = 0

    cards[name] += int(num)
    return cards

def main(filename):
    cards_mainboard = {}
    cards_sideboard = {}
    exceptions = set()
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "mtggoldfish.com/deck" in line:
                main, side = get_list_from_goldfish(line)
            else:
                raise(Exception("Requires goldfish decks"))

            for card in main:
                card = card.strip()
                if not card:
                    continue

                try:
                    cards_mainboard = add_card_to_cards(card, cards_mainboard)
                except Exception as e:
                    exceptions.add(card)
                    continue

            for card in side:
                card = card.strip()
                if not card:
                    continue

                try:
                    cards_sideboard = add_card_to_cards(card, cards_sideboard)
                except Exception as e:
                    exceptions.add(card)
                    continue

    sorted_cards_mainboard = sorted(cards_mainboard.items(), key=operator.itemgetter(1), reverse=True)
    with open("exports/{}_mainboards.txt".format(filename.strip('.txt')), "w") as f:
        for card in sorted_cards_mainboard:
            f.write('{} {}\n'.format(card[0], card[1]))

    sorted_cards_sideboard = sorted(cards_sideboard.items(), key=operator.itemgetter(1), reverse=True)
    with open("exports/{}_sideboards.txt".format(filename.strip('.txt')), "w") as f:
        for card in sorted_cards_sideboard:
            f.write('{} {}\n'.format(card[0], card[1]))

    if exceptions:
        print("\n*****Errors:****\n {}\n".format(exceptions))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()
    main(args.input_file)
