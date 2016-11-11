from rest_framework.decorators import api_view, renderer_classes
from rest_framework.views import APIView
from rest_framework import response, schemas, viewsets, status
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from api_rest.models import StorageUnit
from api_rest.datacube.dc_models import DatasetType
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
