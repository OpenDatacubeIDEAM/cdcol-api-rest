from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from api_rest.models import StorageUnit
from StringIO import StringIO
import base64, yaml

class StorageUnitSerializer(serializers.Serializer):

	name = serializers.CharField(max_length=200)
	description = serializers.CharField()
	description_file = serializers.CharField()
	ingest_file = serializers.CharField()
	created_by = serializers.CharField(max_length=200)

	def create(self, validated_data):
		with open('/home/developer/Documentos/description_file.yaml', 'w') as desc_file:
			desc_io = StringIO(validated_data['description_file'].replace('\\n','\n'))
			base64.decode(desc_io, desc_file)
		with open('/home/developer/Documentos/ingest_file.yaml', 'w') as desc_file:
			desc_io = StringIO(validated_data['ingest_file'].replace('\\n','\n'))
			base64.decode(desc_io, desc_file)
		validated_data['metadata'] = ''
		with open('/home/developer/Documentos/description_file.yaml', 'r') as metadata_file:
			metadata = yaml.load(metadata_file)
			validated_data['metadata'] = JSONRenderer().render(metadata)
		return object()
		
