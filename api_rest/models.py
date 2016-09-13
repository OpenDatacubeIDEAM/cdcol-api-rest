from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User

# Create your models here.
class StorageUnit(models.Model):
	name = models.CharField(max_length=200)
	description = models.TextField()
	description_file = models.CharField(max_length=200)
	ingest_file = models.CharField(max_length=200)
	metadata = JSONField()
	root_dir = models.FilePathField()
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "{} - {}".format(self.id, self.name)
