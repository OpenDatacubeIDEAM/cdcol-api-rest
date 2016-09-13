from rest_framework import serializers
from api_rest.models import StorageUnit

class StorageUnitSerializer(serializers.ModelSerializer):
	
	class Meta:
		model = StorageUnit
