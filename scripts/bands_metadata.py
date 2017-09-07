from xml.etree import ElementTree as etree
from xml.etree.ElementTree import SubElement as sub
import sys

vrt_file_path = sys.argv[1]

vrt_data = etree.parse(vrt_file_path)
root_e = vrt_data.getroot()

metadata_e = sub(root_e, 'Metadata')

for each_path in sys.argv[2:]:
	band_name, band_number = each_path.rsplit('.',3)[1:3]
	mdi_e = sub(metadata_e, 'MDI')
	mdi_e.set('key','band_' + band_number)
	mdi_e.text = band_name

vrt_data.write(vrt_file_path)

