"""Look into which autoplots have not been used in a while"""
from __future__ import print_function
import re

import pandas as pd
from pyiem.util import get_dbconn

QRE = re.compile("q=([0-9]+)")
NO_FEATURES = [
    17,  # is referenced by canonical page
    38,  # radiation plot that is complex
    49, 50, 51,   # cscap plots that should be removed
    110, 111, 112, 113, 114, 115, 116, 117,
    118, 119, 120, 121, 122, 123, 124,   # climodat text-only reports
    143, 141,  # yieldfx plots
    152,  # growing season differences, too noisey
    96,  # one-off showing precip biases
    94,  # one-off showing temp biases
    102,  # LSR report types
    187  # Unimplemented
]


def main():
    """DO Something"""
    pgconn = get_dbconn('mesosite', user='nobody')
    cursor = pgconn.cursor()

    cursor.execute("""SELECT valid, appurl from feature WHERE appurl is not null
        and appurl != ''
        """)
    rows = {}
    for row in cursor:
        appurl = row[1]
        valid = row[0]
        if appurl.find("/plotting/auto/") != 0:
            continue
        tokens = QRE.findall(appurl)
        if not tokens:
            print("appurl: %s valid: %s failed RE" % (appurl, valid))
            continue
        appid = int(tokens[0])
        if appid in NO_FEATURES:
            continue
        res = rows.setdefault(appid, valid)
        if res < valid:
            rows[appid] = valid

    if not rows:
        print("No data found")
        return
    df = pd.DataFrame.from_dict(rows, orient='index')
    df.columns = ['valid']
    maxval = df.index.max()
    for i in range(1, maxval):
        if i not in rows and i not in NO_FEATURES:
            print("No entries for: %4i" % (i, ))
    df.sort_values(by='valid', inplace=True)
    print(df.head(10))


if __name__ == '__main__':
    main()
