<?php
include("../../../../config/settings.inc.php");
include("$rootpath/include/database.inc.php");
$date = isset($_GET["date"]) ? $_GET["date"] : date("Y-m-d", time() - 86400 - (7 * 3600));
$var = (isset($_GET["var"]) && $_GET["var"] != "" ) ? $_GET["var"] : "c11";
$var2 = (isset($_GET["var2"]) && $_GET["var2"] != "" ) ? $_GET["var2"] : "";
$direct = isset($_GET["direct"]) ? $_GET['direct']: "";

dl($mapscript);
include("$rootpath/include/agclimateLoc.php");

function mktitlelocal($map, $imgObj, $titlet) { 
 
  $layer = $map->getLayerByName("credits");
 
     // point feature with text for location
  $point = ms_newpointobj();
  $point->setXY( 0, 10);
  $point->draw($map, $layer, $imgObj, 0,
    $titlet ."                                                           ");
  $point->free();

     // point feature with text for location
  $point = ms_newpointobj();
  $point->setXY( 0, 330);
  $point->draw($map, $layer, $imgObj, 1,
    "  Iowa Environmental Mesonet | Iowa State Ag Climate Network ");
  $point->free();
}

function plotNoData($map, $img){
  $layer = $map->getLayerByName("credits");

  $point = ms_newpointobj();
  $point->setXY( 100, 200);
  $point->draw($map, $layer, $img, 1,
    "  No data found for this date! ");
  $point->free();

}

  $ts = strtotime($date);


$varDef = Array("c11" => "High Air Temperatures",
  "c12" => "Low Air Temperatures [F]",
  "c11c12" => "High and Low Air Temperatures [F]",
  "c30" => "Avg 4in Soil Temperatures [F]",
  "c40" => "Avg Wind Velocity [MPH]",
  "c509" => "Peak 1 Minute Gust [MPH]",
  "c529" => "Peak 5 Second Gust [MPH]",
  "c930" => "Total Precipitation [inch]",
  "c90" => "Total Precipitation [inch]",
  "c20" => "Avg Relative Humidity",
  "c80" => "Solar Radiation [Langleys]",
  "c70" => "Evapotranspiration [inch]",
  "c300hc300l" => "High and Low 4in Soil Temps [F]",
  "c529c530" => "Peak 5 Second Wind Gust and Time [MPH] [CST]",
  "dwpfhdwpfl" => "Max and Min Dew Points [F]"
);

$rnd = Array("c11" => 0, "c12" => 0, "c30" => 0,"c300h" => 0, "c300l" => 0,
  "c70" => 2, "c40" => 1 ,"c80" => 0, "dwpfl" => 0, "dwpfh" => 0,
  "c90" => 2,
  "c529" => 0,
  "c530" => 2,
  "pmonth" => 2,
  "pday" => 2);


$myStations = $ISUAGcities;
$height = 350;
$width = 450;

$proj = "proj=tmerc,lat_0=41.5,lon_0=-93.65,x_0=0,y_0=0,k=0.9999";

$map = ms_newMapObj("base.map");
$map->setProjection($proj);

$map->setextent(-252561, -133255, 300625, 277631);


$counties = $map->getlayerbyname("counties");
$counties->set("status", MS_ON);

$snet = $map->getlayerbyname("snet");
$snet->set("status", MS_ON);
$sclass = $snet->getClass(0);

$iards = $map->getlayerbyname("iards");
$iards->set("status", 1);


$ponly = $map->getlayerbyname("pointonly");
$ponly->set("status", MS_ON);

$img = $map->prepareImage();
$counties->draw($img);
$iards->draw($img);

$c = iemdb("isuag");
$tbl = strftime("t%Y", $ts);
$dstamp = strftime("%Y-%m-%d", $ts);
if ($var == 'c300') {
  $q = "SELECT station, max(c300) as c300h, max(c300_f) as c300h_f,
     min(c300) as c300l, max(c300_f) as c300l_f
     from ${tbl}_hourly WHERE date(valid) = '${dstamp}' GROUP by station";
  $var = 'c300h';
  $var2 = 'c300l';
} else if ($var == 'dwpf') {
  $q = "select MAX( k2f( dewpt( f2k(c100), c200)))::numeric(7,2) as dwpfh,
      station, MIN( k2f( dewpt( f2k(c100), c200)))::numeric(7,2) as dwpfl,
      max(c100_f) as dwpfh_f, max(c100_f) as dwpfl_f
      from ${tbl}_hourly WHERE c200 > 0 and date(valid) = '${dstamp}' GROUP by station";
  $var = 'dwpfh';
  $var2 = 'dwpfl';
} else if ($var == "c529") {
  $q = "SELECT station, c529, c529_f, 
    substring(c530,length(c530) - 3,2) || ':' || 
    substring(c530, length(c530) - 1,2) as c530 , 
    c530_f from ${tbl}_daily WHERE valid = '${dstamp}' ";
  $var2 = 'c530';
} else {
  $q = "SELECT * from ${tbl}_daily WHERE valid = '${dstamp}' ";
}  
$rs =  pg_exec($c, $q);
$data = Array();
for ($i=0; $row = @pg_fetch_array($rs,$i); $i++) {
  $key = $row['station'];
  if ($key == "A133259" || $key == "A130219") continue;
  $data[$key] = Array();
  $data[$key]['city'] = $ISUAGcities[$key]['city'];
  $data[$key]['lon'] = $ISUAGcities[$key]['lon'];
  $data[$key]['lat'] = $ISUAGcities[$key]['lat'];
  //print_r($row);
  //echo "::$var::";
  $data[$key]['var'] = $row[$var];

  // Red Dot... 
  $pt = ms_newPointObj();
  $pt->setXY($ISUAGcities[$key]['lon'], $ISUAGcities[$key]['lat'], 0);
  $pt->draw($map, $ponly, $img, 0, ' ' );
  $pt->free();

  // Value UL
  $pt = ms_newPointObj();
  $pt->setXY($ISUAGcities[$key]['lon'], $ISUAGcities[$key]['lat'], 0);
  $pt->draw($map, $snet, $img, 0, 
     round($row[$var], $rnd[$var]) ." ". $row[$var .'_f'] );
  $pt->free();

  if (strlen($var2) > 0) {
    $data[$key]['var2'] = $row[$var2];
    // Value LL
    $pt = ms_newPointObj();
    $pt->setXY($ISUAGcities[$key]['lon'], $ISUAGcities[$key]['lat'], 0);
    if ($var2 == 'c530'){
      $pt->draw($map, $snet, $img, 2, 
        $row[$var2] ." ". $row[$var2 .'_f'] );
    } else {
      $pt->draw($map, $snet, $img, 2, 
        round($row[$var2], $rnd[$var2]) ." ". $row[$var2 .'_f'] );
    }
    $pt->free();
  }

  // City Name
  $pt = ms_newPointObj();
  $pt->setXY($ISUAGcities[$key]['lon'], $ISUAGcities[$key]['lat'], 0);
  $pt->draw($map, $snet, $img, 1, $ISUAGcities[$key]['city'] );
  $pt->free();
}
if ($i == 0)
   plotNoData($map, $img);

mktitlelocal($map, $img, "     ". $varDef[$var . $var2] ." on ". date("d M Y", $ts) ."    ");
$map->drawLabelCache($img);

$url = $img->saveWebImage();

if (strlen($direct) > 0) { 
  header("Content-type: image/png");
  $img->saveImage('');
} else {
?>
<img src="<?php echo $url; ?>" border=1>

<?php } ?>
