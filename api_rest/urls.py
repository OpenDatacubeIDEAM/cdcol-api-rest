from django.conf.urls import url, include
from rest_framework import routers
from api_rest.views import * 

router = routers.DefaultRouter()
router.register(r'storage_units', StorageUnitViewSet, base_name='storage_units')

urlpatterns = [
	url(r'^', include(router.urls)),
	url(r'^storage_units/(?P<stg_unit_id>\d+)/years/$', ContentYearsView.as_view()),
	url(r'^docs/$', schema_view, name='schema_view'),
]
