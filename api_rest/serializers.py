from rest_framework import serializers
from api_rest.models import StorageUnit
from StringIO import StringIO
import base64

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
		return object()
		
