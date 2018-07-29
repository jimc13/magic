import re
import io
import csv
import requests

def get_decklists_from_googlesheet(url):
    sheet_id = re.search(r"""https://docs.google.com/spreadsheets/d/([^/]*)/""", url).group(1)
    r = requests.get("https://docs.google.com/spreadsheets/d/{}/export?format=csv".format(sheet_id))
    r.raise_for_status()
    # Google have an API but it is authenticated so I figured this was simpler
    # As we are interesed in public data we can just grab it the link below already
    # worked most of this out for us
    #http://www.madhur.co.in/blog/2016/05/13/google-docs-spreadsheet.html
    sio = io.StringIO(r.text, newline=None)
    reader = csv.reader(sio, dialect=csv.excel)

    rownum = 0
    decklist_col = None
    decklists = []
    for row in reader:
        if rownum == 0:
            for i, col in enumerate(row):
                if "deck" in col.lower() and "list" in col.lower():
                    assert not decklist_col, "Multiple columns containing decklist found"
                    decklist_col = i
        else:
            assert decklist_col, "Couldn't locate the decklist column"
            decklists.append(row[decklist_col])

        rownum += 1

    return decklists

if __name__ == "main":
    print(get_decklists_from_googlesheet("https://docs.google.com/spreadsheets/d/1LoIzFkkFTXLgOd5ojFjDFZ_WWm7bqcTlbSOMPM9BE0Y/edit?usp=sharing"))
