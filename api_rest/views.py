from rest_framework.decorators import api_view, renderer_classes
from rest_framework import response, schemas, viewsets, status
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from api_rest.models import StorageUnit
from api_rest.serializers import StorageUnitSerializer
from rest_framework.parsers import JSONParser
from StringIO import StringIO
import shutil

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
		instance.delete()
		shutil.rmtree(root_dir)
		return response.Response(data={'status' : 'Storage Unit Deleted' }, status=status.HTTP_204_NO_CONTENT)
