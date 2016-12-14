# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer

# Create your models here.
class StorageUnit(models.Model):
	name = models.CharField(max_length=200, unique=True)
	description = models.TextField()
	description_file = models.CharField(max_length=200)
	ingest_file = models.CharField(max_length=200)
	metadata_generation_script = models.CharField(max_length=200)
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

	class Meta:
		db_table = 'storage_storageunit'

class Topic(models.Model):
	name = models.CharField(max_length=200)
	enabled = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "{} - {}".format(self.id, self.name)

	class Meta:
		db_table = 'algorithm_topic'

class Algorithm(models.Model):
	name = models.CharField(max_length=200)
	description = models.TextField()
	topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='algorithm_author')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "{} - {}".format(self.id, self.name)

	class Meta:
		db_table = 'algorithm_algorithm'

def upload_to(new_version, filename):
	return "uploads/versions/source_code/{}/{}".format(new_version.id, filename)

class Version(models.Model):
	DEVELOPED_STATE = '1'
	PUBLISHED_STATE = '2'
	DEPRECATED_STATE = '3'
	# PUBLISHING STATES
	VERSION_STATES = (
		(DEVELOPED_STATE, "EN DESARROLLO"),
		(PUBLISHED_STATE, "PUBLICADA"),
		(DEPRECATED_STATE, "OBSOLETA"),
	)
	algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE)
	source_storage_units = models.ManyToManyField(StorageUnit, through='VersionStorageUnit')
	description = models.TextField()
	number = models.CharField(max_length=200)
	repository_url = models.CharField(max_length=300)
	source_code = models.FileField(upload_to=upload_to, blank=True, null=True)
	publishing_state = models.CharField(max_length=2, choices=VERSION_STATES)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='version_author')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "{} - {} {}".format(self.id, self.algorithm.name, self.number)

	class Meta:
		db_table = 'algorithm_version'

class VersionStorageUnit(models.Model):
	version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name='source_version')
	storage_unit = models.ForeignKey(StorageUnit, on_delete=models.CASCADE, related_name='source_storage_unit')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "{} - {}".format(self.version.name, self.storage_unit.name)

	class Meta:
		db_table = 'algorithm_versionstorageunit'

class Execution(models.Model):
	ENQUEUED_STATE = '1'
	EXECUTING_STATE = '2'
	ERROR_STATE = '3'
	COMPLETED_STATE = '4'
	CANCELED_STATE = '5'
	EXECUTION_STATES = (
		(ENQUEUED_STATE, "EN ESPERA"),
		(EXECUTING_STATE, "EN EJECUCIÓN"),
		(ERROR_STATE, "CON FALLO"),
		(COMPLETED_STATE, "FINALIZADA"),
		(CANCELED_STATE, "CANCELADA"),
	)
	version = models.ForeignKey(Version, on_delete=models.CASCADE)
	description = models.TextField(blank=True, null=True)
	state = models.CharField(max_length=2, choices=EXECUTION_STATES)
	started_at = models.DateTimeField()
	finished_at = models.DateTimeField(blank=True, null=True)
	trace_error = models.TextField(blank=True, null=True)
	executed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='execution_author')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "{} - {} - v{}".format(self.id, self.version.algorithm.name, self.version.number)

	class Meta:
		db_table = 'execution_execution'

class Task(models.Model):
	PENDING_STATE = '1'
	RECEIVED_STATE = '2'
	STARTED_STATE = '3'
	SUCCESS_STATE = '4'
	FAILURE_STATE = '5'
	REVOKED_STATE = '6'
	RETRY_STATE = '7'
	TASK_STATES = (
		(PENDING_STATE, "PENDIENTE"),
		(RECEIVED_STATE, "RECIBIDO"),
		(STARTED_STATE, "INICIADO"),
		(SUCCESS_STATE, "EXITOSO"),
		(FAILURE_STATE, "CON FALLO"),
		(REVOKED_STATE, "ANULADO"),
		(RETRY_STATE, "REINTENTO"),
	)
	execution = models.ForeignKey(Execution, on_delete=models.CASCADE)
	uuid = models.CharField(max_length=100)
	start_date = models.DateField()
	end_date = models.DateField()
	state = models.CharField(max_length=2, choices=TASK_STATES)
	state_updated_at = models.DateTimeField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "{} - {}".format(self.execution.id, self.uuid)

	class Meta:
		db_table = 'execution_task'
