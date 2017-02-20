# EGCG Reporting App
[![travis](https://img.shields.io/travis/EdinburghGenomics/Reporting-App/master.svg)](https://travis-ci.org/EdinburghGenomics/Reporting-App)
[![landscape](https://landscape.io/github/EdinburghGenomics/Reporting-App/master/landscape.svg)](https://landscape.io/github/EdinburghGenomics/Reporting-App)
[![GitHub issues](https://img.shields.io/github/issues/EdinburghGenomics/Reporting-App.svg)](https://github.com/EdinburghGenomics/Reporting-App/issues)

(Note: this project uses EGCG-Core, which is available [here](https://github.com/EdinburghGenomics/EGCG-Core.git).)

This project contains the companion Rest API and web app for
[Analysis-Driver](https://github.com/EdinburghGenomics/Analysis-Driver).


## Rest API
This consists of an Eve/Flask JSON API with aggregation and Clarity Lims extensions. There are three main
components:

### \_\_init\_\_
Contains the main Eve app. Configurations are supplied via egcg_core.config and settings.py.

#### configurations
Settings.py helps set up the schema from `etc/schema.yaml`, as well as NoSQL connections and url prefixes if
the app is being run on Tornado.

#### endpoints

Vanilla Eve - these can be filtered by any field in the schema.
- __runs__ - Container for run_elements and analysis_driver_procs for demultiplexing runs.
- __lanes__ - Groups run_elements by lane.
- __run_elements__ - Represents a single combination of a sample id, lane and sequencing barcode. Contains
  demultiplexing QC data.
- __unexpected_barcodes__ - Record of any unexpected barcodes found during demultiplexing.
- __projects__ - Container for samples and analysis_driver_procs for per-sample relatedness checks.
- __samples__ - Contains analysis_driver_procs for sample processing and related QC data. Also contains
  information on data delivery/deletion.
- __analysis_driver_procs__ - Records of pipeline runs. Can be associated with a run, sample or project.
- __analysis_driver_stages__ - Records of stages within a pipeline run. Currently used for reporting on
  pipeline performance, but will eventually be used for Luigi pipeline segmentation.

Pipeline aggregation - these can be filtered by any field in the schema or dynamically generated during
aggregation (see `aggregation/database_side/queries.py`).
- __run_elements_by_lane__ - Aggregates all run_elements per sequencing lane.
- __all_runs__ - Displays runs with associated run_elements.
- __run_elements__ - Basic aggregation per run element.
- __samples__ - As all_runs, but for samples.
- __projects__ - Displays projects with associated samples.

Lims queries - certain parameters can be passed per query.
- __status/<status_type>__ - Calls sqlalchemy queries in limsdb.


### aggregation
- server_side - Used for relatively simple aggregation and dynamic calculation of fields. `queries.py`
  specifies aggregation workflows using expressions (e.g, Sum, Percentage, etc.) from `expressions.py`. This
  aggregation is called automatically via Eve event hooks. Also contains `post_processing.py`, which performs
  any aggregation functions not available in MongoDB aggregation for `aggregation/database_side`.
- database_side - Used in situations where it is necessary to filter on aggregated fields. Uses MongoDB's
  aggregation pipeline feature. The pipelines in `queries.py` are passed to PyMongo via `collection.aggregate`.
  `stages.py` contains shorthand convenience functions for complex/repetitive pipeline stages. For more
  information, see the [MongoDB docs](https://docs.mongodb.com/manual/core/aggregation-pipeline/).

### limsdb
Uses sqlalchemy to query the Clarity database directly and generate predetermined views of the Lims.
Sqlalchemy expressions in `__init__.py` are passed to `sample_status.py` and `run_status.py`, where the
unprocessed SQL joins are rolled into sensibly-formed JSON data.

- __sample_status__ - Displays samples with 'Prep Workflow' and 'Species' UDFs. Request args:
  `?match={"project_id":<project_id>}` filters by project id, `?match={"sample_id":<sample_id>}` filters by
  sample name, and `?detailed=True/False` specifies whether to limit information returned for processes the
  sample is queued in.
- __project_status__ - Samples grouped per project.
- __plate_status__ - Samples grouped per plate.
- __run_status__ - Finds recent sequencing runs and displays run status, instrument ID and associated
  projects/samples. Request args: `?status=current` displays currently running sequencers, `?status=recent`
  displays recently-completed runs, and no args displays a combination of the two.


## Reporting App
This is a Flask app that uses/displays the information from `rest_api`. Pages are generated using Jinja
templating, Datatables and Bootstrap.

Authentication is implemented via `flask_login`. A database of users is specified in the reporting app config
in `user_db`. Users can be added, removed and reset with the admin functions in `auth.py`.


## auth
Contains classes used in `flask_login` to implement authentication. On the reporting app, a user logs in and
generates an auth token, which allows them to authenticate with the Rest API underneath as well. To allow
this, there is a DualAuth class here, which allows users to supply username/password credentials or an auth
token.


## etc
- __column_mappings__ - Column configurations for datatables, including column id, column header name, the
  column's location in the Rest API JSON data, and any Javascript post processing to be applied.
- __project_status_definitions__ - Helper config for the aggregation of data from `limsdb`, defining what a
  sample should be marked as, depending on which workflows it has or has not been through.
- __schema.yaml__ - Passed to Eve as the schema/data validation layer. For more information, see the
  [Eve docs](http://python-eve.org/config.html#schema).


## database_versioning
Currently, this contains database migration scripts for instances where the schema is altered, rather than
simply added to.


## docker
Dockerfile and template config for building the Rest API component as a Docker image. To build the image,
navigate to this directory and run:

`docker build -t <image_name> .`

It is possible to do this without altering `reporting.yaml`, but there would not be any valid Lims connection.
There are two ways to fix this: you can either edit `reporting.yaml` before building, or supply a different
config at run time using Docker volumes.

Having built the image, you should now be able to run a container and query its Rest API through `egcg_core`:

    $ docker run <image_name>
    $ docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container_name>
    <prints container IP address>
    $ python
    >>> from egcg_core.rest_communication import Communicator
    >>> c = Communicator(('username', 'password'), 'http://<container_ip_address>/api/0.1')
    >>> c.get_documents('run_elements', where={'run_id': 'a_run'}, max_results=4)

By default, when an image is started up it will pull the latest version of EdinburghGenomics/Reporting-App on
`master`. To change what version/branch/tag is checked out, you can supply a single positional argument after
the image name.

If you start up a container as above with no volumes mounted, the Rest API will use an internal user database
at /opt/users.sqlite and an internal NoSQL database at the MongoDB default location of /data/db. You can keep
the container completely isolated like this, or link it to databases on your host system with Docker volumes.

For example, to start a container with our own databases and tag v0.9.2 of the app:

    docker run -v path/to/my_user_db.sqlite:/opt/users.sqlite -v path/to/my_nosql_db:/data/db <image_name> v0.9.2


## Dependencies
- a running MongoDB database
- sqlite3 with associated C libraries
- sqlalchemy with associated C libraries


## Running the reporting app
Although the app and Rest API are in the same repository, they are to be run separately. This can be done in
one of two ways:
- __Tornado__ - Run Python on `bin/run_app.py` with the argument `reporting_app` or `rest_api`
- __Apache__ - Write a WSGI script for each app, for example:

```python
import sys
sys.path.append('/var/www/Reporting-App')
# set up config file env vars, etc/

import reporting_app
# set up logging, etc.

application = reporting_app.app
```
