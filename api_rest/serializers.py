from rest_framework import serializers
from django.contrib.auth.models import User
from api_rest.models import StorageUnit
from StringIO import StringIO
import base64, yaml, os

class StorageUnitSerializer(serializers.Serializer):

	name = serializers.CharField(max_length=200)
	description = serializers.CharField()
	description_file = serializers.CharField()
	ingest_file = serializers.CharField()
	metadata = serializers.JSONField(required=False)
	root_dir = serializers.CharField(required=False)
	created_by = serializers.CharField(max_length=200)
	created_at = serializers.DateTimeField(required=False)
	updated_at = serializers.DateTimeField(required=False)

	def create(self, validated_data):

		if StorageUnit.objects.filter(name=validated_data['name']).exists():
			raise serializers.ValidationError('The Storage Unit Already Exists')

		stg_unit_folder = os.environ['DC_STORAGE'] + '/' + validated_data['name'].upper()

		if not os.path.exists(stg_unit_folder):
			os.makedirs(stg_unit_folder)

		validated_data['root_dir'] = stg_unit_folder

		desc_file_path = stg_unit_folder + '/description_file.yml'
		with open(desc_file_path , 'w') as desc_file:
			desc_io = StringIO(validated_data['description_file'].replace('\\n','\n'))
			base64.decode(desc_io, desc_file)
			validated_data['description_file'] = desc_file_path

		ingest_file_path = stg_unit_folder + '/ingest_file.yml'
		with open(ingest_file_path, 'w') as ingest_file:
			desc_io = StringIO(validated_data['ingest_file'].replace('\\n','\n'))
			base64.decode(desc_io, ingest_file)
			validated_data['ingest_file'] = ingest_file_path

		validated_data['metadata'] = ''
		with open(stg_unit_folder + '/description_file.yml', 'r') as metadata_file:
			metadata = yaml.load(metadata_file)
			validated_data['metadata'] = metadata

		validated_data['created_by'] = User.objects.get(id=validated_data['created_by'])

		return StorageUnit.objects.create(**validated_data)
