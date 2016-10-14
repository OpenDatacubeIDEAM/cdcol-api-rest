from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer

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
		return "{}".format(self.name)

	def print_all(self):
		print 'Name: ' + self.name
		print 'Description: ' + self.description
		print 'Description file: ' + self.description_file
		print 'Ingest file: ' + self.ingest_file
		print 'Metadata: ' + JSONRenderer().render(self.metadata)
		print 'Root directory: ' + self.root_dir
		print 'Created by: ' + self.created_by.username
		if self.created_at is None:
			print 'Created at: None'
		else:
			print 'Created at: ' + str(self.created_at)
		if self.updated_at is None:
			print 'Updated at: None'
		else:
			print 'Updated at: ' + str(self.updated_at)
