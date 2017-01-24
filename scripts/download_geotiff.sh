#!/bin/bash
#Script para la generación de thumbnails de resultados, 
#debería ser llamado por el cron que revisa el estado de la ejecución, 
#cuando encuentra que una ejecución ha terminado correctamente.
#Parámetros Opcionales:Carpeta resolución

#GDAL_DATA Debería estar definida en el entorno, si no, toca definirla.
export GDAL_DATA="${GDAL_DATA:-/usr/share/gdal/1.11}"

PYTHON=python

FILE="$1"
BN=`basename $FILE`
FOLDER="${1%/$BN}"
WITH_BANDS_NAME=false
METADATA_SCRIPT= # Metadata generation script

if `gdalinfo $FILE |grep -q "SUBDATASET.*"`
then
	for ds in `gdalinfo $FILE | grep -E "NETCDF.*"`
	do
	band_number=$(echo $ds | sed -e 's/^[^0-9]*\([0-9]*\).*/\1/')
	echo "Escribiendo el archivo $FILE y la banda ${ds##*\:} ($band_number)"
	# gdal_translate  -a_srs EPSG:32618 -stats -of PNG -scale -ot Byte -outsize $RES $RES $ds $TN_FOLDER/${bn%.nc}.${ds##*\:}.png
	gdal_translate -a_srs EPSG:32618 -stats ${ds#*\=} $FOLDER/${BN%.nc}.${ds##*\:}.$band_number.tiff
	done
	WITH_BANDS_NAME=true
else
	
	nb=`gdalinfo $FILE |grep  Band|wc -l`
	echo $nb 
	if [[ $nb -le 1 ]]
	then
		echo "Escribiendo el thumbnail para el archivo $FILE"
		# gdal_translate  -a_srs EPSG:32618  -stats -of PNG -scale -ot Byte -outsize $RES $RES $FILE $TN_FOLDER/${bn%.nc}.png
		gdal_translate -a_srs EPSG:32618 -stats $FILE $FOLDER/${BN%.nc}.tiff
	else
		for i in $(seq 1 $nb)
		do
		echo "Escribiendo el thumbnail para el archivo $FILE banda $i"

		gdal_translate -a_srs EPSG:32618 -stats $FILE $FOLDER/${BN%.nc}.$i.tiff
		done
	fi
fi

GEOTIFF_FILES=$(ls ${FILE%.*}.*.tiff | sed -e 's/\(^.*\.\([0-9]*\)\.tiff\)/\2_\1/' | sort -t _ -k 1 -n | sed -e 's/^[0-9]*_\(.*\)/\1/')
if [ $WITH_BANDS_NAME = false ]
then
	gdal_merge.py -separate -o ${FILE%.*}.tiff $GEOTIFF_FILES
else
	VRT_FILE=$FOLDER/geotiff.vrt
	gdalbuildvrt -separate $VRT_FILE $GEOTIFF_FILES
	$PYTHON $METADATA_SCRIPT $VRT_FILE $GEOTIFF_FILES
	gdal_translate $VRT_FILE ${FILE%.*}.tiff
fi
rm ${FILE%.*}.*.tiff
