from rest_framework.decorators import api_view, renderer_classes
from rest_framework import response, schemas, viewsets
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from api_rest.models import StorageUnit
from api_rest.serializers import StorageUnitSerializer

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

