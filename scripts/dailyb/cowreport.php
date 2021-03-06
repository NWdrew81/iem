<?php
/*
 * Print a report of IEM Cow statistics
 * This is called from the python spammer script as it uses the output to
 * send in an email
 */
date_default_timezone_set('America/Chicago');

/* Generate some cow statistics! */
$ets = mktime(0,0,0,date("m"),date("d"),date("Y"));
$sts = $ets - 86400.0;
date_default_timezone_set('UTC');

include("../../include/cow.php");
include("../../include/database.inc.php");
$cow = new Cow( iemdb("postgis") );
$cow->setLimitTime( $sts, $ets );
$cow->setHailSize(1.0);
$cow->setLimitType( Array("TO","SV") );
$cow->setLimitLSRType( Array("TO","SV") );
$cow->milk();

if (sizeof($cow->warnings) == 0){ echo "No Warnings Issued\n"; die(); }

echo sprintf("SVR+TOR Warnings Issued: %s Verified: %s  [%.1f %%]\n", 
     sizeof($cow->warnings), $cow->computeWarningsVerified(),
     $cow->computeWarningsVerifiedPercent() );
echo sprintf("Reduction of Size Versus County Based     [%.1f %%]\n",
     $cow->computeSizeReduction() );
echo sprintf("Average Perimeter Ratio                   [%.1f %%]\n",
     $cow->computeAveragePerimeterRatio() );
echo sprintf("Percentage of Warned Area Verified (15km) [%.1f %%]\n",
     $cow->computeAreaVerify() );
echo sprintf("Average Storm Based Warning Size          [%.0f sq km]\n",
     $cow->computeAverageSize() );
echo sprintf("Probability of Detection(higher is better)[%.2f]\n",
     $cow->computePOD() );
echo sprintf("False Alarm Ratio (lower is better)       [%.2f]\n",
     $cow->computeFAR() );
echo sprintf("Critical Success Index (higher is better) [%.2f]\n",
     $cow->computeCSI() );

?>
