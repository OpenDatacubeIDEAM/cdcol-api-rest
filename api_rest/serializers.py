from rest_framework import serializers
from django.contrib.auth.models import User
from api_rest.models import StorageUnit
from StringIO import StringIO
import base64, yaml, os, subprocess
from subprocess import CalledProcessError

class StorageUnitSerializer(serializers.Serializer):

	id = serializers.IntegerField(required=False)
	name = serializers.CharField(max_length=200)
	description = serializers.CharField()
	description_file = serializers.CharField()
	ingest_file = serializers.CharField()
	metadata_generation_script = serializers.CharField()
	metadata = serializers.JSONField(required=False)
	root_dir = serializers.CharField(required=False)
	created_by = serializers.CharField(max_length=200)
	created_at = serializers.DateTimeField(required=False)
	updated_at = serializers.DateTimeField(required=False)

	def _b64_to_bin(self, file_path, file_name, b64str):

		try:
			with open(file_path + '/' + file_name , 'w') as output_file:
				str_io = StringIO(b64str.replace('\\n','\n'))
				base64.decode(str_io, output_file)
				return file_name
		except:
			return None

	def create(self, validated_data):

		if StorageUnit.objects.filter(name=validated_data['name']).exists():
			raise serializers.ValidationError('The Storage Unit Already Exists')

		stg_unit_folder = os.environ['DC_STORAGE'] + '/' + validated_data['name'].upper()

		if not os.path.exists(stg_unit_folder):
			os.makedirs(stg_unit_folder)

		validated_data['root_dir'] = stg_unit_folder

		validated_data['description_file'] = self._b64_to_bin(stg_unit_folder, 'description_file.yml', validated_data['description_file'])
		validated_data['ingest_file'] = self._b64_to_bin(stg_unit_folder, 'ingest_file.yml', validated_data['ingest_file'])
		validated_data['metadata_generation_script'] = self._b64_to_bin(stg_unit_folder, 'mgen_script.py', validated_data['metadata_generation_script'])

		validated_data['metadata'] = ''
		with open(stg_unit_folder + '/' + validated_data['description_file'], 'r') as metadata_file:
			metadata = yaml.load(metadata_file)
			validated_data['metadata'] = metadata.get('metadata')

		validated_data['created_by'] = User.objects.get(id=validated_data['created_by'])

		try:
			subprocess.check_output(['datacube', 'product', 'add', stg_unit_folder + '/' + validated_data['description_file']])
		except CalledProcessError as cpe:
			print "Error creating the storage unit; " + str(cpe)
			raise serializers.ValidationError('Error creating the Storage Unit in the Data Cube')

		return StorageUnit.objects.create(**validated_data)
