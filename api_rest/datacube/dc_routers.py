class DatacubeRouter(object):

	def __init__(self):

		self.dc_models = [
		'Dataset',
		'DatasetLocation',
		'DatasetSource',
		'DatasetType',
		'MetadataType'
		]

	def db_for_read(self, model, **hints):

		if model._meta.label.split('.',1)[-1] in self.dc_models:
			return 'datacube'
		return None

	def db_for_write(self, model, **hints):

		if model._meta.label.split('.',1)[-1] in self.dc_models:
			return 'datacube'
		#	return None
		return None
