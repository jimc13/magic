import requests
import re
import operator
import codecs
from parse_goldfish import get_list_from_goldfish, add_card_to_cards
from get_csv_data_from_google_sheet import get_decklists_from_googlesheet

def main(url):
    decklists = get_decklists_from_googlesheet(url)
    repr_main = {"//main", "//main-1", "Main:", "MB:", "Mainboard", "MB", "//deck", "//deck-1", "//Mainboard", "Maindeck (60):", "//Creatures:", "//Creatures", "//Spells", "//Lands", "//Lands:", "//Sorceries:", "//Planeswalkers:", "//Artifacts:"}
    repr_side = {"//sideboard", "Side:", "Sideboard (15):", "Sideboard //", "// 15 Sideboard", "//sideboard-1", "SB:", "SB", "Sideboard", "Sideboard:", "Sideboard//", "//Sideboard:", "Side Board", "SIDEBOARD","//Sideboard"}
    repr_break = {"//maybe-1", "//token-1"}
    cards_mainboard = {}
    cards_sideboard = {}
    exceptions = set()
    for i, decklist in enumerate(decklists):
        main = []
        side = []
        if "mtggoldfish.com/deck" in decklist:
            main, side = get_list_from_goldfish(decklist)
        else:
            # Fairly lazy way to make this run on Windows, I'm happy \r\n
            # will always represent a newline in our input data
            decklist.replace('\r\n', '\n')
            # If there is only one double newline we can be confident that
            # it separate's the side and mainboard
            try:
                # confirm this passes my stuff ok
                maintext, sidetext = decklist.split('\n\n', -1)
                main = maintext.split('\n')
                side = sidetext.split('\n')
            except:
                pass

            # If the above failed try to split the main and sideboard in a more
            # complex way
            if not main and not side:
                add_to = main
                decklist = decklist.split('\n')
                set_decklist = set(decklist)
                if not repr_side.intersection(set(decklist)):
                    # A sideboard isn't required but warn as this may cause issues
                    # Add 2: lists start at 0; first row of csv is the key
                    exceptions.add("Assumed all cards from row {} were from mainboard as couldn't separate it from the sideboard".format(i+2))

                for card in decklist:
                    if card in repr_main:
                        add_to = main
                    elif card in repr_side:
                        add_to = side
                    elif card in repr_break:
                        # If a maybe board or list of tokens are supplied we
                        # shouldn't add them to either the side or mainboard
                        # We assume that this will always be at the bottom of
                        # the deck
                        break
                    else:
                        # Decklists should only contain meta data such as Deck
                        # Sideboard and a list of cards
                        add_to.append(card)

        for card in main:
            if not card:
                continue
            if card in repr_main:
                continue
            try:
                cards_mainboard = add_card_to_cards(card, cards_mainboard)
            except Exception:
                exceptions.add(card)
                continue

        for card in side:
            if not card:
                continue
            if card in repr_side:
                continue
            try:
                cards_sideboard = add_card_to_cards(card, cards_sideboard)
            except Exception:
                exceptions.add(card)
                continue

    sorted_cards_mainboard = sorted(cards_mainboard.items(), key=operator.itemgetter(1), reverse=True)
    sorted_cards_sideboard = sorted(cards_sideboard.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_cards_mainboard, sorted_cards_sideboard, exceptions

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    name = re.search(r"""<meta property="og:title" content="(.*?)">""", requests.get(args.url).text).group(1).replace(" ", "_").lower()
    sorted_cards_mainboard, sorted_cards_sideboard, exceptions = main(args.url)
    with codecs.open("exports/{}_mainboards.txt".format(name), "w", "utf-8-sig") as f:
        for card in sorted_cards_mainboard:
            f.write('{} {}\r\n'.format(card[1], card[0]))

    with codecs.open("exports/{}_sideboards.txt".format(name), "w", "utf-8-sig") as f:
        for card in sorted_cards_sideboard:
            f.write('{} {}\r\n'.format(card[1], card[0]))

    if exceptions:
        print("\n*****Errors:****\n {}\n".format(exceptions))
