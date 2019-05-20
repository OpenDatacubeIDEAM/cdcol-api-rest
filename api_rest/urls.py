from django.conf.urls import url, include
from rest_framework import routers
from api_rest.views import * 


app_name = 'api_rest'

router = routers.DefaultRouter()
router.register(r'storage_units', StorageUnitViewSet, base_name='storage_units')

urlpatterns = [
	url(r'^', include(router.urls)),
	url(r'^storage_units/(?P<stg_unit_id>\d+)/years/$', ContentYearsView.as_view()),
	url(r'^storage_units/(?P<stg_unit_id>\d+)/years/(?P<year>\d+)/$', ContentLongLatView.as_view()),
	url(r'^storage_units/(?P<stg_unit_id>\d+)/years/(?P<year>\d+)/(?P<lon_lat>[\w.-]+)/$', ContentImagesView.as_view()),
	url(r'^storage_units/(?P<stg_unit_id>\d+)/contents/(?P<image_name>[\w-]+\.nc)/$', ContentsView.as_view()),
	url(r'^new_execution/', NewExecutionView.as_view()),
	url(r'^download_geotiff/', DownloadGeotiff.as_view()),
	url(r'^cancel_execution/', CancelExecutionView.as_view()),
	url(r'^algorithms/publish/', PublishNewAlgorithmView.as_view()),
]
