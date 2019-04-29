from rest_framework import serializers
from django.contrib.auth.models import User
from api_rest.models import StorageUnit, Execution, Task, Version
from io import StringIO
import base64, yaml, os, subprocess, datetime, json
from subprocess import CalledProcessError
from importlib import import_module
from urllib.request import urlopen
from jinja2 import Environment, FileSystemLoader
import zipfile
from airflow.bin import cli
from airflow import models,settings
import argparse, glob
import shutil
from slugify import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class StorageUnitSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    alias = serializers.CharField(max_length=200)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField()
    description_file = serializers.FileField()
    ingest_file = serializers.FileField()
    metadata_generation_script = serializers.FileField()
    metadata = serializers.JSONField(required=False)
    root_dir = serializers.CharField(required=False)
    created_by = serializers.CharField(max_length=200)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)

    def create(self, validated_data):

        dc_storage_path = os.environ['DC_STORAGE']
        to_ingest_path = os.environ['TO_INGEST']
        web_thumbnails_path = os.environ['WEB_THUMBNAILS']

        storage_unit_name = validated_data['name']

        if StorageUnit.objects.filter(name=storage_unit_name).exists():
            raise serializers.ValidationError('The Storage Unit Already Exists')

        stg_unit_folder = os.path.join(dc_storage_path, storage_unit_name)
        to_ingest_folder = os.path.join(to_ingest_path, storage_unit_name)
        web_thumb_folder = os.path.join(web_thumbnails_path, storage_unit_name)

        if not os.path.exists(stg_unit_folder):
            os.makedirs(stg_unit_folder)

        if not os.path.exists(to_ingest_folder):
            os.makedirs(to_ingest_folder)

        if not os.path.exists(web_thumb_folder):
            os.makedirs(web_thumb_folder)

        descrip_mfile = validated_data['description_file']
        ingest_mfile = validated_data['ingest_file']
        meta_gen_script_mfile = validated_data['metadata_generation_script']

        descrip_path = os.path.join(stg_unit_folder, 'description_file.yml')
        ingest_path = os.path.join(stg_unit_folder, 'ingest_file.yml')
        meta_gen_script_path = os.path.join(stg_unit_folder, 'mgen_script.py')

        # Save files into the dc_storage
        with open(descrip_path, 'wb') as dfile:
            dfile.write(descrip_mfile.read())

        with open(ingest_path, 'wb') as ifile:
            ifile.write(ingest_mfile.read())

        with open(meta_gen_script_path, 'wb') as mfile:
            mfile.write(meta_gen_script_mfile.read())

        validated_data['root_dir'] = stg_unit_folder
        ingest_file_path = os.path.join(stg_unit_folder, 'ingest_file.yml')

        validated_data['metadata'] = ''
        with open(ingest_file_path, 'r') as metadata_file:
            metadata = yaml.load(metadata_file)
            validated_data['metadata'] = {}
            validated_data['metadata']['measurements'] = []
            for each_band in metadata.get('measurements'):
                band = {}
                band['name'] = each_band['name']
                band['src_varname'] = each_band['src_varname']
                validated_data['metadata']['measurements'].append(band)

        validated_data['created_by'] = User.objects.get(id=validated_data['created_by'])
        description_file_path = os.path.join(stg_unit_folder, 'description_file.yml')

        try:
            subprocess.check_output(
                ['/home/cubo/anaconda/bin/datacube', 'product', 'add', description_file_path]
            )
        except CalledProcessError as cpe:
            print("Error creating the storage unit; " + str(cpe))
        # raise serializers.ValidationError('Error creating the Storage Unit in the Data Cube')

        validated_data['description_file'] = 'description_file.yml'
        validated_data['ingest_file'] = 'ingest_file.yml'
        validated_data['metadata_generation_script'] = 'mgen_script.py'

        return StorageUnit.objects.create(**validated_data)


class ExecutionSerializer(serializers.Serializer):
    PARAM_TYPES = {
        'STRING_TYPE': '1',
        'INTEGER_TYPE': '2',
        'DOUBLE_TYPE': '3',
        'BOOLEAN_TYPE': '4',
        'AREA_TYPE': '7',
        'STORAGE_UNIT_TYPE': '8',
        'TIME_PERIOD_TYPE': '9',
        'FILE_TYPE': '12',
        'STORAGE_UNIT_SIMPLE_TYPE': '13'
    }

    execution_id = serializers.IntegerField()
    algorithm_name = serializers.CharField(max_length=200)
    version_id = serializers.CharField(max_length=200)
    parameters = serializers.JSONField()
    is_gif = serializers.BooleanField()

    def get_product(self, param_dict):
        for keys in param_dict.keys():
            if param_dict[keys]['type'] == self.PARAM_TYPES['STORAGE_UNIT_TYPE']:
                return [param_dict[keys]['storage_unit_name']], param_dict[keys]['bands'].split(',')
            elif param_dict[keys]['type'] == self.PARAM_TYPES['STORAGE_UNIT_SIMPLE_TYPE']:
                return [param_dict[keys]['storage_unit_name']], []

    def get_area(self, param_dict):
        for keys in param_dict.keys():
            if param_dict[keys]['type'] == self.PARAM_TYPES['AREA_TYPE']:
                return int(param_dict[keys]['longitude_start']), int(param_dict[keys]['longitude_end']), int(param_dict[keys][
                    'latitude_start']), int(param_dict[keys]['latitude_end'])

    def get_time_periods(self, param_dict):
        time_periods = []
        for keys in param_dict.keys():
            if param_dict[keys]['type'] == self.PARAM_TYPES['TIME_PERIOD_TYPE']:
                time_periods.append((param_dict[keys]['start_date'], param_dict[keys]['end_date']))
        return time_periods

    def get_kwargs(self, param_dict):
        kwargs = {}
        for keys in param_dict.keys():
            if param_dict[keys]['type'] == self.PARAM_TYPES['STRING_TYPE']:
                kwargs[keys] = param_dict[keys]['value']
            elif param_dict[keys]['type'] == self.PARAM_TYPES['INTEGER_TYPE']:
                kwargs[keys] = int(param_dict[keys]['value'])
            elif param_dict[keys]['type'] == self.PARAM_TYPES['DOUBLE_TYPE']:
                kwargs[keys] = float(param_dict[keys]['value'])
            elif param_dict[keys]['type'] == self.PARAM_TYPES['BOOLEAN_TYPE']:
                if param_dict[keys]['value'] == 'True' or param_dict[keys]['value'] == 'true':
                    kwargs[keys] = True
                elif param_dict[keys]['value'] == 'False' or param_dict[keys]['value'] == 'false':
                    kwargs[keys] = False
                else:
                    kwargs[keys] = bool(param_dict[keys]['value'])
            elif param_dict[keys]['type'] == self.PARAM_TYPES['FILE_TYPE']:
                kwargs[keys] = param_dict[keys]['value']
        return kwargs

    def create(self, validated_data):

        # TODO: Importar Jinja 2
        # TODO: Crear el diccionario
        execution = Execution.objects.get(pk=validated_data['execution_id'])

        min_long, max_long, min_lat, max_lat = self.get_area(validated_data['parameters'])
        params = dict(self.get_kwargs(validated_data['parameters']))
        params['lat'] = (min_lat, max_lat)
        params['lon'] = (min_long, max_long)
        params['products'], params['bands'] = self.get_product(validated_data['parameters'])
        params['time_ranges'] = self.get_time_periods(validated_data['parameters'])
        params['execID'] = 'execution_{}_{}_{}'.format(str(validated_data['execution_id']),
                                                       validated_data['algorithm_name'], validated_data['version_id'])
        params['elimina_resultados_anteriores'] = True
        params['genera_mosaico'] = True
        # params['owner'] = Execution.executed_by.
        params['owner'] = "API-REST"
        # TODO: Cargar el template

        template_path = os.path.join(os.environ['TEMPLATE_PATH'], slugify(validated_data['algorithm_name']))
        generic_template_path = os.path.join(os.environ['TEMPLATE_PATH'], "generic-template")

        if execution.version is not None and execution.version.publishing_state == Version.PUBLISHED_STATE and os.path.exists(template_path):
            file_loader = FileSystemLoader(template_path)
            env = Environment(loader=file_loader)
            algorithm_template_path = '{}_{}.py'.format(slugify(validated_data['algorithm_name']),
                                                        validated_data['version_id'])
            template = env.get_template(algorithm_template_path)
        else:
            file_loader = FileSystemLoader(generic_template_path)
            env = Environment(loader=file_loader)
            algorithm_template_path = '{}_{}'.format("generic-template", "1.0")
            params['algorithm_name'] = slugify(validated_data['algorithm_name'])
            params['version_id'] = validated_data['version_id']
            template = env.get_template(algorithm_template_path)

        # TODO: Renderizar el template
        airflow_dag_path = os.environ['AIRFLOW_DAG_PATH']
        execution_dag_path = '{}/execution_{}_{}_{}.py'.format(airflow_dag_path, str(validated_data['execution_id']),
                                                               slugify(validated_data['algorithm_name']),
                                                               validated_data['version_id'])
        output = template.render(params=params)
        with open(execution_dag_path, 'w') as dag:
            dag.write(output)
        dag.close()
        execution.dag_id = params['execID']
        execution.save()

        # TODO: Ejecutar workflow
        bash_command1 = '/home/cubo/anaconda/bin/airflow list_dags'
        bash_command2 = '/home/cubo/anaconda/bin/airflow unpause' + params['execID']

        subprocess.call(bash_command1.split())
        subprocess.call(bash_command2.split())

        dagbag = models.DagBag(settings.DAGS_FOLDER)
        dagbag.collect_dags()
        dagbag.process_file(self, filepath=execution_dag_path)

        args = argparse.Namespace()
        args.dag_id = params['execID']
        args.run_id = None
        args.exec_id = None
        args.conf = None
        args.exec_date = None
        args.subdir = None
        cli.set_is_paused(False, args=args)
        cli.trigger_dag(args)




        # TODO: Modificar la ejecución en la base de datos

        # time_ranges = self.get_time_periods(validated_data['parameters'])
        #
        # gtask_parameters = {}
        # gtask_parameters['execID'] = str(validated_data['execution_id'])
        # gtask_parameters['algorithm'] = validated_data['algorithm_name']
        # gtask_parameters['version'] = validated_data['version_id']
        # gtask_parameters['output_expression'] = ''
        # gtask_parameters['product'], gtask_parameters['bands'] = self.get_product(validated_data['parameters'])
        # gtask_parameters = dict(self.get_kwargs(validated_data['parameters']), **gtask_parameters)
        #
        # gtask = import_module(os.environ['GEN_TASK_MOD'])
        # # flower = os.environ['FLOWER']

        # for key in gtask_parameters:
        #	print 'param \'' + key + '\': ' + str(gtask_parameters[key])

        # result = gtask.generic_task(min_long=min_long, min_lat=min_lat, **gtask_parameters)

        # if validated_data['is_gif']:
        #     gtask_parameters['min_lat'] = int(min_lat)
        #     gtask_parameters['min_long'] = int(min_long)
        #     result = group(
        #         gtask.generic_task.s(time_ranges=[("01-01-" + str(A), +"31-12-" + str(A))], **gtask_parameters) for A in
        #         xrange(int(time_ranges[0][0].split('-')[2]), int(time_ranges[0][1].split('-')[2]) + 1)).delay()
        #     for each_result in result.results:
        #         new_task = {
        #             'uuid': each_result.id,
        #             'state': '1',
        #             'execution_id': gtask_parameters['execID'],
        #             'state_updated_at': str(datetime.datetime.now()),
        #             'created_at': str(datetime.datetime.now()),
        #             'updated_at': str(datetime.datetime.now()),
        #             'start_date': str(datetime.date.today()),
        #             'end_date': str(datetime.date.today()),
        #
        #         }
        #         Task.objects.create(**new_task)
        # else:
        #     gtask_parameters['time_ranges'] = time_ranges
        #     result = group(gtask.generic_task.s(min_lat=Y, min_long=X, **gtask_parameters) for Y in
        #                    xrange(int(min_lat), int(max_lat)) for X in xrange(int(min_long), int(max_long))).delay()
        #     for each_result in result.results:
        #         # try:
        #         # 	task = json.loads(urlopen(flower + '/api/task/info/'+each_result.id).read())
        #         # except:
        #         # 	task = {'kwargs':''}
        #         new_task = {
        #             'uuid': each_result.id,
        #             'state': '1',
        #             'execution_id': gtask_parameters['execID'],
        #             'state_updated_at': str(datetime.datetime.now()),
        #             'created_at': str(datetime.datetime.now()),
        #             'updated_at': str(datetime.datetime.now()),
        #             'start_date': str(datetime.date.today()),
        #             'end_date': str(datetime.date.today()),
        #             # 'parameters': json.dumps(each_result.__dict__),
        #         }
        #         Task.objects.create(**new_task)

        return validated_data


class AlgorithmSerializer(serializers.Serializer):
    version_id = serializers.IntegerField(required=False)
    algorithms_zip_file = serializers.FileField()
    template_file = serializers.FileField()

    def create(self, validated_data):
        extraction_path = os.path.join(os.environ['DOWNLOAD_PATH'], str(validated_data["version_id"]))
        version = Version.objects.get(pk=validated_data["version_id"])

        with zipfile.ZipFile(validated_data["algorithms_zip_file"], "r") as file_to_extract:
            file_to_extract.extractall(extraction_path)

        # TODO: Poner el template en la carpeta templates
        template_path = os.path.join(os.environ['TEMPLATE_PATH'], slugify(version.algorithm.name))

        if not os.path.isdir(template_path):
            os.makedirs(template_path)

        with open(os.path.join(template_path, "{}_{}.py".format(slugify(version.algorithm.name), version.number)),
                  'wb') as tfile:
            tfile.write(validated_data["template_file"].read())
        tfile.close()

        # TODO: Poner los algoritmos en la caprta de algoritmos
        for file in os.listdir(extraction_path):
            if os.path.isdir(os.path.join(extraction_path, file)):
                algorithm_path = os.path.join(os.environ['WORKFLOW_ALGORITHMS_PATH'], file)
                if not os.path.isdir(algorithm_path):
                    os.makedirs(algorithm_path)

                python_files = glob.glob(os.path.join(extraction_path, file, "*.py"))
                if not python_files:
                    raise serializers.ValidationError(
                        'No hay algoritmos en esta carpeta: {}'.format(os.path.join(extraction_path, file, "*.py")))
                for alg_file in os.listdir(os.path.join(extraction_path, file)):
                    if alg_file.endswith(".py"):
                        # TODO: Revisar que no hayan algoritmos con el mismo nombre
                        if os.path.exists(os.path.join(algorithm_path, alg_file)):
                            raise serializers.ValidationError('El algoritmo {} ya existe en la carpeta {}'.format(file,
                                                                                                                  os.path.join(
                                                                                                                      algorithm_path,
                                                                                                                      alg_file)))
                        else:
                            with open(os.path.join(algorithm_path, alg_file), 'wb') as afile:
                                f = open(os.path.join(extraction_path, file, alg_file), "rb")
                                afile.write(f.read())
                            f.close()
                            afile.close()
            else:
                raise serializers.ValidationError('Cada algoritmo debería ir en su carpeta')

        shutil.rmtree(extraction_path)
        return validated_data
