# -*- coding: utf-8 -*-

from rest_framework.decorators import api_view, renderer_classes
from rest_framework.views import APIView
from rest_framework import response, schemas, viewsets, status
from api_rest.models import StorageUnit, Task, Execution, VersionStorageUnit
from api_rest.datacube.dc_models import DatasetType, DatasetLocation, Dataset
from api_rest.serializers import StorageUnitSerializer, ExecutionSerializer, AlgorithmSerializer
from rest_framework.parsers import JSONParser
from io import StringIO
import shutil, os, re, glob, yaml, subprocess
from subprocess import CalledProcessError
from airflow import models,settings
from airflow.api.common.experimental import mark_tasks
from airflow.models import DagRun
import shutil
import datetime

# Create your views here.
class StorageUnitViewSet(viewsets.ModelViewSet):
	queryset = StorageUnit.objects.all()
	serializer_class = StorageUnitSerializer
	
	# def perform_create(self, serializer):
	# 	if type(self.request.data) is dict:
	# 		json_content = self.request.data
	# 	elif type(self.request.data) is str:
	# 		json_str = self.request.data
	# 		json_io = StringIO(json_str)
	# 		json_content = JSONParser().parse(json_io)
	# 	serializer = StorageUnitSerializer(data=json_content)
	# 	if serializer.is_valid():
	# 		storage_unit = serializer.save()
	# 		serializer = StorageUnitSerializer(storage_unit)
	# 		return response.Response(data=serializer.data, status=status.HTTP_201_CREATED)

	def perform_destroy(self, instance):
		root_dir = instance.root_dir
		stg_name = instance.name
		try:
			DatasetType.objects.filter(name=instance.name)[0].delete()
		except IndexError:
			print('Nothing to delete on the database')
		instance.delete()
		shutil.rmtree(root_dir)
		shutil.rmtree(os.environ['TO_INGEST'] + '/' + stg_name)
		return response.Response(data={'status' : 'Storage Unit Deleted' }, status=status.HTTP_204_NO_CONTENT)


class ContentYearsView(APIView):

	def get(self, request, stg_unit_id):
		stg_unit_name = StorageUnit.objects.filter(id=stg_unit_id).get().name
		files = glob.glob(os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/*.nc')
		years = set()
		for each_file in files:
			years.add(re.sub(r'^.*_([0-9]{4})[0-9]*\.nc',r'\1',each_file))
		return response.Response(data={ 'years' : years }, status=status.HTTP_200_OK)

class ContentLongLatView(APIView):

	def get(self, request, stg_unit_id, year):
		if re.match(r'[0-9]{4}$', str(year)):
			stg_unit_name = StorageUnit.objects.filter(id=stg_unit_id).get().name
			files = glob.glob(os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/*.nc')
			ingest_file = yaml.load(open(os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/ingest_file.yml','r'))
			base_lon =ingest_file.get('storage')['tile_size']['longitude']
			base_lat =ingest_file.get('storage')['tile_size']['latitude']
			coordinates = []
			lon_lat = set()
			for each_file in files:
				if re.search(r'^.*_([\-0-9]*)_([\-0-9]*)_' + re.escape(year) + r'[0-9]*\.nc', each_file) is not None:
					lon_lat.add(re.sub(r'^.*_([\-0-9]*)_([\-0-9]*)_' + re.escape(year) + r'[0-9]*\.nc',r'\1;\2',each_file))
			for each_lon_lat in lon_lat:
				lon, lat = each_lon_lat.split(';')
				coordinates.append({'longitude': (int(lon) * base_lon), 'latitude': (int(lat) * base_lat)})
			return response.Response(data={ 'coordinates' : coordinates }, status=status.HTTP_200_OK)
		else:
			return response.Response(data={ 'status' : 'El año debe ser un entero de 4 digitos' }, status=status.HTTP_400_BAD_REQUEST)

class ContentImagesView(APIView):

	def get(self, request, stg_unit_id, year, lon_lat):
		if re.match(r'[0-9]{4}$', str(year)) and re.match(r'[-]{0,1}[0-9]+[.]{1}[0-9]+_[-]{0,1}[0-9]+[.]{1}[0-9]+', lon_lat):
			stg_unit_name = StorageUnit.objects.filter(id=stg_unit_id).get().name
			files = glob.glob(os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/*.nc')
			images = []
			ingest_file = yaml.load(open(os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/ingest_file.yml','r'))
			base_lon =ingest_file.get('storage')['tile_size']['longitude']
			base_lat =ingest_file.get('storage')['tile_size']['latitude']
			lon, lat = lon_lat.split('_',1)
			lon = int(float(lon)/base_lon)
			lat = int(float(lat)/base_lat)
			for each_file in files:
				if re.search(r'^.*_' + re.escape(str(lon) + '_' + str(lat)) + '_' + re.escape(year) + r'[0-9]*\.nc',each_file) is not None:
					images.append(re.sub(r'.*/([^/]*$)',r'\1',each_file))
			return response.Response(data={'images' : images }, status=status.HTTP_200_OK)
		else:
			errors = []
			if re.match(r'[0-9]{4}$', str(year)) is None:
				errors.append('El año debe ser un entero de 4 digitos')
			if re.match(r'[-]{0,1}[0-9]+_[-]{0,1}[0-9]+', lon_lat) is None:
				errors.append('Las coordenadas longitud_latitud deben ser decimales separados por un guion bajo')
			return response.Response(data={ 'status' : errors }, status=status.HTTP_400_BAD_REQUEST)

class ContentsView(APIView):

	def get(self, request, stg_unit_id, image_name):
		if re.match(r'[^/]*.nc', str(image_name)):
			stg_unit_alias = StorageUnit.objects.filter(id=stg_unit_id).get().alias
			stg_unit_name = StorageUnit.objects.filter(id=stg_unit_id).get().name
			image = os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/' + image_name
			metadata = DatasetLocation.objects.filter(uri_body__contains=image).get().dataset_ref.metadata
			ingest_file = yaml.load(open(os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/ingest_file.yml','r'))
			base_lon =ingest_file.get('storage')['tile_size']['longitude']
			base_lat =ingest_file.get('storage')['tile_size']['latitude']
			lon, lat, year = re.sub(r'^.*_([\-0-9]*)_([\-0-9]*)_([0-9]{4})[0-9]*\.nc',r'\1;\2;\3', image_name).split(';',2)
			lon = int(lon) * base_lon
			lat = int(lat) * base_lat
			thumbnails = {}
			for each_thumbnail in glob.glob(os.environ['WEB_THUMBNAILS'] + '/' + stg_unit_name + '/' + image_name.replace('.nc','') + '*.png'):
				thumbnails[re.sub(r'^.*\.([^.]*)\.png$',r'\1',each_thumbnail)] = each_thumbnail
			return response.Response(data={ 'image_uri' : image,
											'metadata' : metadata,
											'coordinates': { 'longitude':lon, 'latitude':lat},
											'year':int(year),
											'thumbnails':thumbnails,
											'storage_unit':stg_unit_name,
											'storage_unit_alias': stg_unit_alias,
											'image_name':image_name
											}, status=status.HTTP_200_OK)
		else:
			response.Response(data={ 'status' : 'El formato del archivo no corresponde o contiene caracteres inválidos.' }, status=status.HTTP_400_BAD_REQUEST)

class NewExecutionView(APIView):

	def post(self, request):

		serializer = ExecutionSerializer(data=request.data)
		print(request.data)
		if serializer.is_valid():
			serializer.save()
			return response.Response(serializer.data, status=status.HTTP_201_CREATED)
		return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CancelExecutionView(APIView):
	def post(self, request):
		execution_id=request.data['execution_id']
		execution = Execution.objects.get(pk=execution_id)
		if execution is not None:
			dagbag = models.DagBag(settings.DAGS_FOLDER)
			dag = dagbag.get_dag(execution.dag_id)
			dr_list = DagRun.find(dag_id=execution.dag_id)
			dr = dr_list[-1]
			try:
				mark_tasks.set_dag_run_state_to_failed(dag=dag, execution_date=dr.execution_date, commit=True)
				return response.Response(data=execution_id, status=status.HTTP_200_OK)
			except:
				return response.Response(data=execution_id, status=status.HTTP_400_BAD_REQUEST)
			shutil.rmtree(os.path.join(os.environ['RESULTS']),execution.dag_id)
			# try:
			# 	tasks = Task.objects.filter(execution_id=execution_id)
			# 	for t in list(tasks):
			# 		revoke(t.uuid)
			# 	return response.Response(data=execution_id, status=status.HTTP_200_OK)
			# except:
			# 	return response.Response(data=execution_id, status=status.HTTP_400_BAD_REQUEST)

		else:
			return response.Response(data=execution_id, status=status.HTTP_404_NOT_FOUND)

class PublishNewAlgorithmView(APIView):
	def post(self, request):
		serializer = AlgorithmSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return response.Response(serializer.data, status=status.HTTP_200_OK)
		return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DownloadGeotiff(APIView):

	def post(self, request):

		if os.path.isfile(request.data['file_path'].replace('.nc','.tiff')):
			return response.Response(data = { 'message' : 'El archivo GeoTiff ya existe', 'file_path' : request.data['file_path'].replace('.nc','.tiff') }, status=status.HTTP_200_OK)
		else:
			try:
				subprocess.check_output([os.environ['TIFF_CONV_SCRIPT'], request.data['file_path']])
				return response.Response(data = { 'message' : 'Archivo transformado correctamente a GeoTiff', 'file_path' : request.data['file_path'].replace('.nc','.tiff') }, status=status.HTTP_200_OK)
			except CalledProcessError as cpe:
				if cpe.returncode == 1:
					return response.Response(data = { 'message' : 'Archivo transformado correctamente a GeoTiff', 'file_path' : request.data['file_path'].replace('.nc','.tiff') }, status=status.HTTP_200_OK)
				else:
					return response.Response(data = { 'message' : 'Error al convertir el archivo' }, status=status.HTTP_400_BAD_REQUEST)
