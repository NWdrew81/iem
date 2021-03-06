"""Generalized mesosite archive_begin computation

For backends that implement alldata(station, valid)"""
from __future__ import print_function
import sys
import datetime

import pytz
from pyiem.network import Table as NetworkTable
from pyiem.util import get_dbconn


def main(argv):
    """Go Main"""
    (dbname, network) = argv[1:]
    basets = datetime.datetime.now()
    basets = basets.replace(tzinfo=pytz.timezone("America/Chicago"))

    pgconn = get_dbconn(dbname)
    rcursor = pgconn.cursor()
    mesosite = get_dbconn('mesosite')
    mcursor = mesosite.cursor()

    table = NetworkTable(network)

    rcursor.execute("""SELECT station, min(valid), max(valid) from alldata
                    GROUP by station ORDER by min ASC""")
    for row in rcursor:
        station = row[0]
        if station not in table.sts:
            continue
        if table.sts[station]['archive_begin'] != row[1]:
            print(('Updated %s STS WAS: %s NOW: %s'
                   '') % (station, table.sts[station]['archive_begin'],
                          row[1]))

        mcursor.execute("""UPDATE stations SET archive_begin = %s
             WHERE id = %s and network = %s""", (row[1], station, network))
        if mcursor.rowcount == 0:
            print('ERROR: No rows updated')

    mcursor.close()
    mesosite.commit()
    mesosite.close()


if __name__ == '__main__':
    main(sys.argv)
