import requests
import re
import operator
import codecs
from parse_goldfish import get_list_from_goldfish, add_card_to_cards
from get_csv_data_from_google_sheet import get_decklists_from_googlesheet

def line_in_set(line, set_to_match):
    for pattern_to_match in set_to_match:
        if re.match(r'^(//)?(\d )?{}(-1)?( \(\d+\))?:?$'.format(pattern_to_match), line, flags=re.M|re.I):
            return True

    return False

def main(url):
    decklists = get_decklists_from_googlesheet(url)
    repr_main = {"main", "mainboard", "mb", "md", "deck", "main ?deck", "creatures?", "spells", "lands?", "sorceries", "planeswalkers", "artifacts", "instant", "sorcery", "enchantments?", "Starts in Deck - .* cards", "- Mainboard \(60\) - "}
    repr_side = {"side ?board", "side", "sb", "------------------------------", "_____SB:", "- Sideboard \(15\) - ", "Sideboard ", "// Sideboard"}
    repr_break = {"//maybe-1", "//token-1", "Added Tokens for Convenience:"}
    repr_ignore = {"// Turbo Ninja", "==========", "2f54f", "Companion"}
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
            decklist = decklist.replace('\r\n', '\n')
            # If there is only one double newline we can be confident that
            # it separate's the side and mainboard
            try:
                l = decklist
                # If there is just the one newline in the middle we can strip
                # all the other crap
                # Lazily using l for the list so we don't overwrite it for the
                # next bit, maybe we could use more than 1 function :P
                for m in repr_main:
                    l = re.sub(r'^(//)?(\d )?{}(-1)?( \(\d+\))?:?$'.format(m), '', l, flags=re.M|re.I)

                for s in repr_side:
                    l = re.sub(r'^(//)?(\d )?{}(-1)?( \(\d+\))?:?$'.format(s), '', l, flags=re.M|re.I)

                for ig in repr_ignore:
                    l = re.sub(r'^(//)?(\d )?{}(-1)?( \(\d+\))?:?$'.format(ig), '', l, flags=re.M|re.I)

                l = l.strip()
                try:
                    maintext, sidetext = l.split('\n\n', -1)
                except:
                    maintext, sidetext = l.split('\n \n', -1)
                main = maintext.split('\n')
                side = sidetext.split('\n')
            except:
                pass

            # If the above failed try to split the main and sideboard in a more
            # complex way
            if not main and not side:
                add_to = main
                decklist = decklist.strip()
                decklist = decklist.split('\n')
                set_decklist = set(decklist)
                sb = False
                for line in decklist:
                    if line_in_set(line, repr_side):
                        sb = True
                        break

                if not sb:
                    # A sideboard isn't required but warn as this may cause issues
                    # Add 2: lists start at 0; count the key
                    print(decklist)
                    exceptions.add("Assumed all cards from row {} were from mainboard as couldn't separate it from the sideboard".format(i+2))

                for card in decklist:
                    if line_in_set(card, repr_main):
                        add_to = main
                    elif line_in_set(card, repr_side):
                        add_to = side
                    elif line_in_set(card, repr_break):
                        # If a maybe board or list of tokens are supplied we
                        # shouldn't add them to either the side or mainboard
                        # We assume that this will always be at the bottom of
                        # the deck
                        break
                    elif line_in_set(card, repr_ignore):
                        continue
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
    excepts_to_print = []
    for exception in exceptions:
        remove = False
        for to_ignore in repr_main, repr_side, repr_break, repr_ignore:
            for pattern_to_remove in to_ignore:
                if re.match(r'^(//)?(\d )?{}(-1)?( \(\d+\))?:?$'.format(pattern_to_remove), exception, flags=re.M|re.I):
                    remove = True

        if not remove:
            excepts_to_print.append(exception)

    return sorted_cards_mainboard, sorted_cards_sideboard, excepts_to_print

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    print("Downloading doc")
    name = re.search(r"""<meta property="og:title" content="(.*?)">""", requests.get(args.url).text).group(1).replace(" ", "_").lower()
    print("Processing doc")
    sorted_cards_mainboard, sorted_cards_sideboard, excepts_to_print = main(args.url)
    print("Writing output files")
    name = name.replace("(responses)", "")
    name = name.replace(":", "")
    with codecs.open("exports/{}_mainboards.txt".format(name), "w", "utf-8-sig") as f:
        for card in sorted_cards_mainboard:
            f.write('{} {}\r\n'.format(card[1], card[0]))

    with codecs.open("exports/{}_sideboards.txt".format(name), "w", "utf-8-sig") as f:
        for card in sorted_cards_sideboard:
            f.write('{} {}\r\n'.format(card[1], card[0]))

    if excepts_to_print:
        print("\n*****Errors:****\n {}\n".format(excepts_to_print))
