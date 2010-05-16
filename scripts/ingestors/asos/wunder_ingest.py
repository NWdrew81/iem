# Leach Wunderground's archive

import urllib2, cookielib
from pyIEM import iemdb, mesonet
i = iemdb.iemdb()
asos = i['asos']
mesosite = i['mesosite']
import mx.DateTime, csv, time
import sys
from metar import Metar
"""
    EGI  2008-12-18 21:55
"""

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
r = opener.open("http://www.wunderground.com/cgi-bin/findweather/getForecast?setpref=SHOWMETAR&value=1").read()

def doit(stid, now):
  metarPass = 0
  metarFail = 0
  processed = 0
  sqlFail = 0
  url = "http://www.wunderground.com/history/airport/K%s/%s/%-i/%-i/DailyHistory.html?req_city=NA&req_state=NA&req_statename=NA&format=1" % (stid, now.year, now.month, now.day)
  try:
    data = opener.open(url).read()
  except:
    print "Fail STID: %s NOW: %s" % (stid, now)
    return
  lines = data.split("\n")
  headers = {}
  for line in lines: # Skip header
    line = line.replace("<br />", "")
    if line.strip() == "":
      continue
    tokens = line.split(",")
    if len(tokens) < 3:
      continue
    if len(headers.keys()) == 0:
      for i in range(len(tokens)):
        headers[ tokens[i] ] = i
      continue
    mstr = (tokens[headers["FullMetar"]]).strip().replace("'","")
    if mstr[:5] != "METAR":
      continue
    mtr = None
    try:
      mtr = Metar.Metar(mstr, now.month, now.year)
    except:
      pass
    sky = {'skyc1': "", 'skyc2': "", 'skyc3': "",
           'skyl1': "Null", 'skyl2': "Null", 'skyl3': "Null"}
    if mtr is not None:
      metarPass += 1
      gts = mx.DateTime.DateTime( mtr.time.year, mtr.time.month, 
                mtr.time.day, mtr.time.hour, mtr.time.minute)
      tmpf = "Null"
      if (mtr.temp):
        tmpf = mtr.temp.value("F")
      dwpf = "Null"
      if (mtr.dewpt):
        dwpf = mtr.dewpt.value("F")

      sknt = "Null"
      if mtr.wind_speed:
        sknt = mtr.wind_speed.value("KT")
      gust = "Null"
      if mtr.wind_gust:
        gust = mtr.wind_gust.value("KT")

      drct = "Null"
      if mtr.wind_dir and mtr.wind_dir.value() != "VRB":
        drct = mtr.wind_dir.value()

      vsby = "Null"
      if mtr.vis:
        vsby = mtr.vis.value("SM")

      alti = "Null"
      if mtr.press:
        alti = mtr.press.value("IN")

      p01m = 0
      if mtr.precip_1hr:
        p01m = mtr.precip_1hr.value("CM") * 10.0

      # Do something with sky coverage
      for i in range(len(mtr.sky)):
        (c,h,b) = mtr.sky[i]
        sky['skyc%s' % (i+1)] = c
        if h is not None:
          sky['skyl%s' % (i+1)] = h.value("FT")

    else:
      metarFail += 1
      tmpf = tokens[ headers['TemperatureF'] ]
      addon = 0
      if headers.has_key('TimeCST'):
        tstr = tokens[ headers['TimeCST'] ]
      elif headers.has_key('TimeCDT'):
        tstr = tokens[ headers['TimeCDT'] ]
      elif headers.has_key('TimeEDT'):
        tstr = tokens[ headers['TimeEDT'] ]
        addon = mx.DateTime.RelativeDateTime(hours=-1)
      elif headers.has_key('TimeEST'):
        tstr = tokens[ headers['TimeEST'] ]
        addon = mx.DateTime.RelativeDateTime(hours=-1)
      ts = mx.DateTime.strptime( '%s %s' % (now.strftime('%Y-%m-%d'), 
           tstr), '%Y-%m-%d %I:%M %p' ) + addon
      gts = ts.gmtime()
      dwpf = tokens[ headers['Dew PointF'] ]
      alti = tokens[ headers['Sea Level PressureIn'] ]
      vsby = tokens[ headers['VisibilityMPH'] ]
      d = tokens[ headers['Wind Direction'] ]
      if d == "Calm" or d == "N/A":
        drct = "Null"
      else:
        drct = mesonet.txt2drct[ tokens[ headers['Wind Direction'] ] ]
      s = tokens[ headers['Wind SpeedMPH'] ]
      if s == "Calm" or s == "N/A":
        sknt = 0
      else:
        sknt = float( s ) / 1.15
      g = tokens[ headers['Gust SpeedMPH'] ]
      if g == "-" or g.strip() == "":
        gust = "Null"
      else:
        gust = float(g) * 1.15
      p = tokens[ headers['PrecipitationIn'] ]
      if p == "N/A" or p.strip() == "":
        p01m = "Null"
      else:
        p01m = float(p) * 25.4

    sql = """INSERT into t%s (station, valid, tmpf, dwpf, vsby, 
        drct, sknt, gust, p01m, alti, skyc1, skyc2, skyc3, 
        skyl1, skyl2, skyl3, metar) values ('%s','%s+00', %s, %s, %s, 
        %s, %s, %s, %s, %s, '%s', '%s', '%s', %s, %s, %s,'%s')""" % (now.year, 
        stid, gts.strftime("%Y-%m-%d %H:%M"), tmpf, dwpf, vsby, drct, 
        sknt, gust, p01m, alti, 
        sky['skyc1'], sky['skyc2'], sky['skyc3'],
        sky['skyl1'], sky['skyl2'], sky['skyl3'], mstr)
    try:
      asos.query(sql)
      processed += 1
    except:
      sqlFail += 1

  #print "%s %s MPASS: %s MFAIL: %s SQLFAIL: %s" % (stid, now, metarPass, 
  #      metarFail, sqlFail)
  return processed

network = sys.argv[1]
# 1. Query for a list of stations to iterate over
rs = mesosite.query("SELECT * from stations WHERE network = '%s'" % (
     network,)).dictresult()
for i in range(len(rs)):
  sid = rs[i]['id']
  # 2. Look in the database for earliest ob with METAR
  rs2 = asos.query("""SELECT min(valid) from alldata WHERE station = '%s'
     and metar is not null""" % (sid,)).dictresult()
  if len(rs2) == 0:
    tend = mx.DateTime.now()
  else:
    tend = mx.DateTime.strptime(rs2[0]['min'][:16], '%Y-%m-%d %H:%M')

  # 3. Move old data to old table
  asos.query("""INSERT into alldata_save SELECT * from alldata WHERE 
   station = '%s' and valid < '%s'""" % (sid, tend.strftime("%Y-%m-%d %H:%M")))
  asos.query("""DELETE from alldata WHERE 
   station = '%s' and valid < '%s'""" % (sid, tend.strftime("%Y-%m-%d %H:%M")))

# 4. Figure out when wunder archive starts and then process till end
  sts = mx.DateTime.DateTime(1970,1,1)
  ets = tend
  now = sts
  tbegin = None
  processed = 0
  while now < ets:
    interval = mx.DateTime.RelativeDateTime(days=1)
    time.sleep(1.3)
    obs = doit(sid, now)
    if obs == 0 and processed == 0:
      interval = mx.DateTime.RelativeDateTime(months=1)
    elif obs > 0 and processed == 0:
      tbegin = now
    processed += obs
    now += interval
  if tbegin is not None:
    print "Station %s Begin: %s Obs: %s" % (sid, tbegin.strftime("%Y-%m-%d"),
      processed)
