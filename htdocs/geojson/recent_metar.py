#!/usr/bin/env python
""" Recent METARs containing some pattern """
import cgi
import json
from json import encoder

import memcache
import psycopg2.extras
from pyiem.util import get_dbconn, ssw
encoder.FLOAT_REPR = lambda o: format(o, '.2f')


def get_data(q):
    """ Get the data for this query """
    pgconn = get_dbconn('iem')
    cursor = pgconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = {"type": "FeatureCollection",
            "crs": {"type": "EPSG",
                    "properties": {"code": 4326,
                                   "coordinate_order": [1, 0]}},
            "features": []}

    # Fetch the values
    if q == 'snowdepth':
        datasql = "substring(raw, ' 4/([0-9]{3})')::int"
        wheresql = "raw ~* ' 4/'"
    elif q == 'fc':
        datasql = "''"
        wheresql = "'FC' = ANY(wxcodes)"
    elif q == 'gr':
        datasql = "''"
        wheresql = "'GR' = ANY(wxcodes)"
    else:
        return json.dumps(data)
    cursor.execute("""
    select id, network, name, st_x(geom) as lon, st_y(geom) as lat,
    valid at time zone 'UTC' as utc_valid,
    """ + datasql + """ as data, raw
    from current_log c JOIN stations t on (c.iemid = t.iemid)
    WHERE network ~* 'ASOS' and """ + wheresql + """ ORDER by valid DESC
    """)
    for i, row in enumerate(cursor):
        data['features'].append({"type": "Feature", "id": i, "properties": {
                "station": row["id"],
                "network": row["network"],
                "name": row["name"],
                "value":  row['data'],
                "metar": row['raw'],
                "valid":  row['utc_valid'].strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "geometry": {"type": "Point",
                         "coordinates": [row['lon'], row['lat']]
                         }
        })
    return json.dumps(data)


def main():
    """ see how we are called """
    field = cgi.FieldStorage()
    q = field.getfirst('q', 'snowdepth')[:10]
    cb = field.getfirst('callback', None)

    ssw("Content-type: application/vnd.geo+json\n\n")

    mckey = ("/geojson/recent_metar?callback=%s&q=%s"
             ) % (cb, q)
    mc = memcache.Client(['iem-memcached:11211'], debug=0)
    res = mc.get(mckey)
    if not res:
        res = get_data(q)
        mc.set(mckey, res, 300)
    if cb is None:
        ssw(res)
    else:
        ssw("%s(%s)" % (cb, res))


if __name__ == '__main__':
    main()
