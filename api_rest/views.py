# -*- coding: utf-8 -*-

from rest_framework.decorators import api_view, renderer_classes
from rest_framework.views import APIView
from rest_framework import response, schemas, viewsets, status
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from api_rest.models import StorageUnit
from api_rest.datacube.dc_models import DatasetType, DatasetLocation, Dataset
from api_rest.serializers import StorageUnitSerializer
from rest_framework.parsers import JSONParser
from StringIO import StringIO
import shutil, os, re, glob

# View for swagger documentation
@api_view()
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request):
	generator = schemas.SchemaGenerator(title='CDCol API')
	return response.Response(generator.get_schema(request=request))

# Create your views here.
class StorageUnitViewSet(viewsets.ModelViewSet):
	queryset = StorageUnit.objects.all()
	serializer_class = StorageUnitSerializer
	
	def perform_create(self, serializer):
		if type(self.request.data) is dict:
			json_content = self.request.data
		elif type(self.request.data) is str:
			json_str = self.request.data
			json_io = StringIO(json_str)
			json_content = JSONParser().parse(json_io)
		serializer = StorageUnitSerializer(data=json_content)
		if serializer.is_valid():
			storage_unit = serializer.save()
			serializer = StorageUnitSerializer(storage_unit)
			return response.Response(data=serializer.data, status=status.HTTP_201_CREATED)

	def perform_destroy(self, instance):
		root_dir = instance.root_dir
		stg_name = instance.name
		DatasetType.objects.filter(name=instance.name)[0].delete()
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
			coordinates = []
			lon_lat = set()
			for each_file in files:
				if re.search(r'^.*_([\-0-9]*)_([\-0-9]*)_' + re.escape(year) + r'[0-9]*\.nc', each_file) is not None:
					lon_lat.add(re.sub(r'^.*_([\-0-9]*)_([\-0-9]*)_' + re.escape(year) + r'[0-9]*\.nc',r'\1;\2',each_file))
			for each_lon_lat in lon_lat:
				lon, lat = each_lon_lat.split(';')
				coordinates.append({'longitude': lon, 'latitude':lat})
			return response.Response(data={ 'coordinates' : coordinates }, status=status.HTTP_200_OK)
		else:
			return response.Response(data={ 'status' : 'El año debe ser un entero de 4 digitos' }, status=status.HTTP_400_BAD_REQUEST)

class ContentImagesView(APIView):

	def get(self, request, stg_unit_id, year, lon_lat):
		if re.match(r'[0-9]{4}$', str(year)) and re.match(r'[-]{0,1}[0-9]+_[-]{0,1}[0-9]+', lon_lat):
			stg_unit_name = StorageUnit.objects.filter(id=stg_unit_id).get().name
			files = glob.glob(os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/*.nc')
			images = []
			for each_file in files:
				if re.search(r'^.*_' + re.escape(lon_lat) + '_' + re.escape(year) + r'[0-9]*\.nc',each_file) is not None:
					images.append(re.sub(r'.*/([^/]*$)',r'\1',each_file))
			return response.Response(data={'images' : images }, status=status.HTTP_200_OK)
		else:
			errors = []
			if re.match(r'[0-9]{4}$', str(year)) is None:
				errors.append('El año debe ser un entero de 4 digitos')
			if re.match(r'[-]{0,1}[0-9]+_[-]{0,1}[0-9]+', lon_lat) is None:
				errors.append('Las coordenadas longitud_latitud deben ser enteros separados por un guion bajo')
			return response.Response(data={ 'status' : errors }, status=status.HTTP_400_BAD_REQUEST)

class ContentsView(APIView):

	def get(self, request, stg_unit_id, image_name):
		if re.match(r'[^/]*.nc', str(image_name)):
			stg_unit_name = StorageUnit.objects.filter(id=stg_unit_id).get().name
			image = os.environ['DC_STORAGE'] + '/' + stg_unit_name + '/' + image_name
			metadata = DatasetLocation.objects.filter(uri_body__contains=image).get().dataset_ref.metadata
			return response.Response(data={ 'image' : image, 'metadata' : metadata }, status=status.HTTP_200_OK)
		else:
			response.Response(data={ 'status' : 'El formato del archivo no corresponde o contiene caracteres inválidos.' }, status=status.HTTP_400_BAD_REQUEST)
