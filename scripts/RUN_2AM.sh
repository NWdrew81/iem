#!/bin/sh
DD=$(date +%d)

cd isuag
sh run_plots.sh
if [ $DD -eq "17" ]
	then
		python nmp_monthly_email.py
fi

# Run the climodat estimator to get sites that are valid at midnight
cd ../climodat
python daily_estimator.py $(date --date '1 days ago' +'%Y %m %d')

cd ../climodat
sh run.sh &
python hrrr_solarrad.py

cd ../coop
if [ $DD -eq "01" ]
	then
	python first_guess_for_harry.py
fi

cd ../util
if [ $DD -eq "02" ]
	then
		sh monthly.sh $(date --date '3 days ago' +'%y %m')
fi

cd ../dl
python download_cfs.py &
# (python download_cfs.py && cd ../yieldfx && python cfs2iemre_netcdf.py && python cfs_tiler.py) & 
if [ $DD -eq "09" ]
	then
		 python download_narr.py $(date --date '13 days ago' +'%Y %m') &
fi


cd ../cache
python warn_cache.py &

cd ../dbutil
python clean_afos.py
python compute_hads_sts.py
python clean_unknown_hads.py
python unknown_stations.py

cd ../ingestors/cocorahs
python redo_day.py IA

cd ../ncdc
if [ $DD -eq "15" ]
	then
	python ingest_fisherporter.py $(date --date '90 days ago' +'%Y %m')
	python ingest_fisherporter.py $(date --date '180 days ago' +'%Y %m')
	python ingest_fisherporter.py $(date --date '360 days ago' +'%Y %m')
fi


cd ../asos_1minute
if [ $DD -eq "09" ]
then
	python parse_ncdc_asos1minute.py
fi


cd ../../windrose
python daily_drive_network.py

cd ../prism
python ingest_prism.py $(date --date '7 days ago' +'%Y %m %d')
python ingest_prism.py $(date --date '60 days ago' +'%Y %m %d')
python ingest_prism.py $(date --date '90 days ago' +'%Y %m %d')
