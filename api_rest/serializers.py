from rest_framework import serializers
from django.contrib.auth.models import User
from api_rest.models import StorageUnit, Execution, Task
from StringIO import StringIO
import base64, yaml, os, subprocess, datetime, json
from subprocess import CalledProcessError
from importlib import import_module
from celery import group

class StorageUnitSerializer(serializers.Serializer):

	id = serializers.IntegerField(required=False)
	alias = serializers.CharField(max_length=200)
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
		except Exception as e:
			print 'Error: ' + str(e)
			return None

	def create(self, validated_data):

		if StorageUnit.objects.filter(name=validated_data['name']).exists():
			raise serializers.ValidationError('The Storage Unit Already Exists')

		stg_unit_folder = os.environ['DC_STORAGE'] + '/' + validated_data['name']
		to_ingest_folder = os.environ['TO_INGEST'] + '/' + validated_data['name']
		web_thumbnails_folder = os.environ['WEB_THUMBNAILS'] + '/' + validated_data['name']

		if not os.path.exists(stg_unit_folder):
			os.makedirs(stg_unit_folder)

		if not os.path.exists(to_ingest_folder):
			os.makedirs(to_ingest_folder)

		if not os.path.exists(web_thumbnails_folder):
			os.makedirs(web_thumbnails_folder)

		validated_data['root_dir'] = stg_unit_folder

		validated_data['description_file'] = self._b64_to_bin(stg_unit_folder, 'description_file.yml', validated_data['description_file'])
		validated_data['ingest_file'] = self._b64_to_bin(stg_unit_folder, 'ingest_file.yml', validated_data['ingest_file'])
		validated_data['metadata_generation_script'] = self._b64_to_bin(stg_unit_folder, 'mgen_script.py', validated_data['metadata_generation_script'])

		validated_data['metadata'] = ''
		with open(stg_unit_folder + '/' + validated_data['ingest_file'], 'r') as metadata_file:
			metadata = yaml.load(metadata_file)
			validated_data['metadata'] = {}
			validated_data['metadata']['measurements'] = []
			for each_band in metadata.get('measurements'):
				band = {}
				band['name'] = each_band['name']
				band['src_varname'] = each_band['src_varname']
				validated_data['metadata']['measurements'].append(band)

		validated_data['created_by'] = User.objects.get(id=validated_data['created_by'])

		try:
			subprocess.check_output(['/home/cubo/anaconda2/bin/datacube', 'product', 'add', stg_unit_folder + '/' + validated_data['description_file']])
		except CalledProcessError as cpe:
			print "Error creating the storage unit; " + str(cpe)
			#raise serializers.ValidationError('Error creating the Storage Unit in the Data Cube')

		return StorageUnit.objects.create(**validated_data)
	
class ExecutionSerializer(serializers.Serializer):

	PARAM_TYPES = {
					'STRING_TYPE':'1',
					'INTEGER_TYPE':'2',
					'DOUBLE_TYPE':'3',
					'BOOLEAN_TYPE':'4',
					'AREA_TYPE':'7',
					'STORAGE_UNIT_TYPE':'8',
					'TIME_PERIOD_TYPE':'9',
					'FILE_TYPE':'12',
					'STORAGE_UNIT_SIMPLE_TYPE':'13'
					}

	execution_id = serializers.IntegerField()
	algorithm_name = serializers.CharField(max_length=200)
	version_id = serializers.CharField(max_length=200)
	parameters = serializers.JSONField()
	is_gif = serializers.BooleanField()

	def get_product(self, param_dict):
		for keys in param_dict.keys():
			if param_dict[keys]['type'] == self.PARAM_TYPES['STORAGE_UNIT_TYPE']:
				return param_dict[keys]['storage_unit_name'], param_dict[keys]['bands'].split(',')
			elif param_dict[keys]['type'] == self.PARAM_TYPES['STORAGE_UNIT_SIMPLE_TYPE']:
				return param_dict[keys]['storage_unit_name'], []

	def get_area(self, param_dict):
		for keys in param_dict.keys():
			if param_dict[keys]['type'] == self.PARAM_TYPES['AREA_TYPE']:
				return param_dict[keys]['longitude_start'], param_dict[keys]['longitude_end'], param_dict[keys]['latitude_start'], param_dict[keys]['latitude_end']

	def get_time_periods(self, param_dict):
		time_periods = []
		for keys in param_dict.keys():
			if param_dict[keys]['type'] == self.PARAM_TYPES['TIME_PERIOD_TYPE']:
				time_periods.append((param_dict[keys]['start_date'], param_dict[keys]['end_date']))
		return time_periods

	def get_kwargs(self, param_dict):
		kwargs = {}
		for keys in param_dict.keys():
			if param_dict[keys]['type'] == self.PARAM_TYPES['STRING_TYPE']:
				kwargs[keys] = param_dict[keys]['value']
			elif param_dict[keys]['type'] == self.PARAM_TYPES['INTEGER_TYPE']:
				kwargs[keys] = int(param_dict[keys]['value'])
			elif param_dict[keys]['type'] == self.PARAM_TYPES['DOUBLE_TYPE']:
				kwargs[keys] = float(param_dict[keys]['value'])
			elif param_dict[keys]['type'] == self.PARAM_TYPES['BOOLEAN_TYPE']:
				kwargs[keys] = bool(param_dict[keys]['value'])
			elif param_dict[keys]['type'] == self.PARAM_TYPES['FILE_TYPE']:
				kwargs[keys] = param_dict[keys]['value']
		return kwargs

	def create(self, validated_data):

		min_long, max_long, min_lat, max_lat = self.get_area(validated_data['parameters'])
		time_ranges = self.get_time_periods(validated_data['parameters'])

		gtask_parameters = {}
		gtask_parameters['execID'] = str(validated_data['execution_id'])
		gtask_parameters['algorithm'] = validated_data['algorithm_name']
		gtask_parameters['version'] = validated_data['version_id']
		gtask_parameters['output_expression'] = ''
		gtask_parameters['product'], gtask_parameters['bands'] = self.get_product(validated_data['parameters'])
		gtask_parameters = dict(self.get_kwargs(validated_data['parameters']), **gtask_parameters)

		gtask = import_module(os.environ['GEN_TASK_MOD'])

		#for key in gtask_parameters:
		#	print 'param \'' + key + '\': ' + str(gtask_parameters[key])

		# result = gtask.generic_task(min_long=min_long, min_lat=min_lat, **gtask_parameters)

		if validated_data['is_gif']:
			gtask_parameters['min_lat'] = int(min_lat)
			gtask_parameters['min_long'] = int(min_long)
			result = group(gtask.generic_task.s(time_ranges=[("01-01-"+str(A),+"31-12-"+str(A))], **gtask_parameters) for A in xrange(int(time_ranges[0][0].split('-')[2]),int(time_ranges[0][1].split('-')[2])+1)).delay()
			for each_result in result.results:
				new_task = {
							'uuid':each_result.id,
							'state':'1',
							'execution_id':gtask_parameters['execID'],
							'state_updated_at':str(datetime.datetime.now()),
							'created_at':str(datetime.datetime.now()),
							'updated_at':str(datetime.datetime.now()),
							'start_date':str(datetime.date.today()),
							'end_date':str(datetime.date.today()),

							}
				Task.objects.create(**new_task)
		else:
			gtask_parameters['time_ranges'] = time_ranges
			result = group(gtask.generic_task.s(min_lat=Y, min_long=X, **gtask_parameters) for Y in xrange(int(min_lat),int(max_lat)) for X in xrange(int(min_long),int(max_long))).delay()
			for each_result in result.results:

				new_task = {
							'uuid':each_result.id,
							'state':'1',
							'execution_id':gtask_parameters['execID'],
							'state_updated_at':str(datetime.datetime.now()),
							'created_at':str(datetime.datetime.now()),
							'updated_at':str(datetime.datetime.now()),
							'start_date':str(datetime.date.today()),
							'end_date':str(datetime.date.today()),
							'parameters':json.dumps(each_result),
							}
				Task.objects.create(**new_task)

		return validated_data
