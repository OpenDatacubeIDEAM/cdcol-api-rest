# Cubo de Datos de Colombia API REST

A continuación se presentan los pasos para configurar el proyecto

## Configuración del ambiente virtual
Se debe instalar el paquete `virtualenv` en el directorio donde clonará el proyecto. Dicho paquete puede ser instalado desde el repositorio del sistema operativo, o alternativamente utilizando `pip`.

```
#!bash
# Utilizando el repositorio de Ubuntu 16.04 LTS para instalar virtualenv
sudo apt-get update && sudo apt-get -y install python python-virtualenv
# Utilizando pip para instalar virtualenv
pip install virtualenv
# Se crea el entorno virtual
virtualenv cdcol
```
Antes de continuar, active el ambiente virtual recién creado.

```
#!bash
# Ingrese al directorio donde se encuentra el ambiente virtual
cd cdcol
# Active el entorno virtual
source bin/activate
```

## Instalación de dependencias

Con el ambiente virtual activado, se deben instalar todas las dependencias para que la aplicación pueda ejecutarse sin inconvenientes.

```
#!bash
# Instalación de dependencias desde el archivo de requerimientos
pip install -r /path/requirements.txt
```

## Configuración de variables de entorno

Para poder ejecutar correctamente los sevicios se requiere que se configuren las variables de entorno del archivo `env_vars`. Para cargar las variables en el sistema es necesario utilizar el comando `source`, de lo contrario no estarán disponibles al iniciar el servicio. Se recomienda cargar las variables al inicio de la sesión del usuario agregando la siguiente línea en el archivo `.profile` o `.bashrc`:
```
#!bash
# Exporta las variables de entorno al iniciar sesión
source /path/to/vars_file/env_vars
```

## Despliegue de prueba

Para probar el despliegue sólo es necesario ejecutar el siguiente comando

```
#!bash
# Utilizando el puerto por defecto aceptando conexiones solamente desde localhost
python manage.py runserver
# Utilizando el puerto 8000 aceptando conexiones desde cualquier dirección
python manage.py runserver 0.0.0.0:8000
```