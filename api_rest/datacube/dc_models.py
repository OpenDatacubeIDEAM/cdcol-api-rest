# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField

class Dataset(models.Model):
    id = models.TextField(primary_key=True)  # This field type is a guess.
    metadata_type_ref = models.ForeignKey('MetadataType', models.DO_NOTHING, db_column='metadata_type_ref')
    dataset_type_ref = models.ForeignKey('DatasetType', models.DO_NOTHING, db_column='dataset_type_ref')
    metadata = JSONField()
    archived = models.DateTimeField(blank=True, null=True)
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset'


class DatasetLocation(models.Model):
    dataset_ref = models.ForeignKey(Dataset, models.DO_NOTHING, db_column='dataset_ref')
    uri_scheme = models.CharField(max_length=-1)
    uri_body = models.CharField(max_length=-1)
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset_location'
        unique_together = (('dataset_ref', 'uri_scheme', 'uri_body'),)


class DatasetSource(models.Model):
    dataset_ref = models.ForeignKey(Dataset, models.DO_NOTHING, db_column='dataset_ref')
    classifier = models.CharField(max_length=-1)
    source_dataset_ref = models.ForeignKey(Dataset, models.DO_NOTHING, db_column='source_dataset_ref')

    class Meta:
        managed = False
        db_table = 'dataset_source'
        unique_together = (('source_dataset_ref', 'dataset_ref'), ('dataset_ref', 'classifier'),)


class DatasetType(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=-1)
    metadata = JSONField()
    metadata_type_ref = models.ForeignKey('MetadataType', models.DO_NOTHING, db_column='metadata_type_ref')
    definition = JSONField()
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dataset_type'


class MetadataType(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=-1)
    definition = JSONField()
    added = models.DateTimeField()
    added_by = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'metadata_type'
