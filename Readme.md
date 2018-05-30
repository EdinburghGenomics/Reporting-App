# EGCG Reporting App
[![travis](https://img.shields.io/travis/EdinburghGenomics/Reporting-App/master.svg)](https://travis-ci.org/EdinburghGenomics/Reporting-App)
[![landscape](https://landscape.io/github/EdinburghGenomics/Reporting-App/master/landscape.svg)](https://landscape.io/github/EdinburghGenomics/Reporting-App)
[![GitHub issues](https://img.shields.io/github/issues/EdinburghGenomics/Reporting-App.svg)](https://github.com/EdinburghGenomics/Reporting-App/issues)
[![Coverage Status](https://coveralls.io/repos/github/EdinburghGenomics/Reporting-App/badge.svg)](https://coveralls.io/github/EdinburghGenomics/Reporting-App)

(Note: this project uses EGCG-Core, which is available [here](https://github.com/EdinburghGenomics/EGCG-Core.git).)

This project contains the companion Rest API and web app for [Analysis-Driver](https://github.com/EdinburghGenomics/Analysis-Driver).


## Rest API
This consists of an Eve/Flask JSON API with aggregation and Clarity Lims extensions. The main Eve app is contained in
`\_\_init\_\_`. Configuration is done by `settings.py`, which sets up the schema from `etc/schema.yaml` as well as NoSQL
connections and url prefixes if the running platform is Tornado.


### Endpoints
- __Vanilla Eve:__ Can be filtered by any field in the schema, or any field contained within `aggregated` (see below).
  - runs: Container for run_elements and analysis_driver_procs for demultiplexing runs.
  - lanes: Groups run_elements by flowcell lane.
  - run_elements: Represents a single combination of a sample id, lane and sequencing barcode. Contains
    demultiplexing QC data.
  - unexpected_barcodes: Record of any unexpected barcodes found during demultiplexing.
  - projects: Container for samples and analysis_driver_procs for per-sample relatedness checks.
  - samples: Contains analysis_driver_procs for sample processing and related QC data. Also contains information on data
    delivery/deletion.
  - analysis_driver_procs: Records of pipeline runs. Can be associated with a run, sample or project.
  - analysis_driver_stages: Records of stages within a pipeline run. Currently used for reporting on
    pipeline performance, but will eventually be used for Luigi pipeline segmentation.

- __[Deprecated] Pipeline aggregation:__ These can be filtered by any field in the schema or dynamically generated during
  aggregation (see `aggregation/database_side/queries.py`).
  - run_elements_by_lane: Aggregates all run_elements per sequencing lane.
  - all_runs: Displays runs with associated run_elements.
  - run_elements: Basic aggregation per run element.
  - samples: As all_runs, but for samples.
  - projects: Displays projects with associated samples.

- __Lims queries:__ Uses SQLAlchemy to query the Clarity database directly and generate predetermined views of the Lims.
  A request gets passed to a SQLAlchemy expression depending on its endpoint, and the unprocessed SQL joins are rolled
  into sensibly-formed JSON data.
  - project_status: Samples aggregated by project.
  - plate_status: Samples aggregated by plate.
  - sample_status: Displays samples with 'Prep Workflow' and 'Species' UDFs. Request args `?match={"project_id":<project_id>}`
    filters by project id, `?match={"sample_id":<sample_id>}` filters by sample name, and `?detailed=True/False`
    specifies whether to limit information returned for processes the sample is queued in.
  - run_status: Finds recent sequencing runs and displays their status, instrument ID and associated projects/samples.
    Request args `?status=current` displays currently running sequencers, `?status=recent`
    displays recently-completed runs, and no args displays a combination of the two.
  - sample_info: Basic sample information
  - project_info: Basic project information


### Aggregation
- __server_side:__: Used for relatively simple aggregation and dynamic calculation of fields. `queries.py`
  specifies aggregation workflows using expressions (e.g, Sum, Percentage, etc.) from `expressions.py`. This
  aggregation is called automatically via Eve event hooks. Also contains `post_processing.py`, which performs
  any aggregation functions not available in MongoDB aggregation for `aggregation/database_side`.
- __[Deprecated] database_side:__ Used in situations where it is necessary to filter on aggregated fields. Uses MongoDB's
  aggregation pipeline feature. The pipelines in `queries.py` are passed to PyMongo via `collection.aggregate`.
  `stages.py` contains shorthand convenience functions for complex/repetitive pipeline stages. For more
  information, see the [MongoDB docs](https://docs.mongodb.com/manual/core/aggregation-pipeline/).
- __database_hooks:__ Aggregates data upon posting or patching of an entity, and stores the results in the subfield
  `aggregated`. Specifies data relations so that, e.g, triggering aggregation in a run_element will re-trigger
   aggregation in all runs and samples it's associated with, and in turn re-trigger aggregation in all corresponding
   projects.


### Actions
This is a module containing code that can be executed with parameters by posting a payload to the endpoint `actions`.
The payload should contain the field `action_type`: `run_review` and `sample_review` initiates a Lims-based sequencing
run or sample review, while `automatic_run_review` and `automatic_sample_review` apply rules from
`etc/review_thresholds.yaml` to a recorded sequencing run or sample. The payload is then passed to a subclass of
`Action` and calls the method `perform_action` on it.


## Reporting App
This is a Flask app that uses/displays the information from `rest_api`. Pages are generated using Jinja
templating, Datatables and Bootstrap. Authentication is implemented via `flask_login`. A database of users is specified in the reporting app config
in `user_db`. Users can be added, removed and reset with the admin functions in `auth.py`.


## Authentication
`auth.py` contains classes used in `flask_login` to implement authentication. On the reporting app, a user logs in and
generates an auth token, which allows them to authenticate with the Rest API underneath as well. To facilitate this,
there is a DualAuth class here, which allows users to supply username/password credentials or an auth token.


## etc
- __column_mappings:__ Column configurations for datatables, including column id, column header name, the
  column's location in the Rest API JSON data, and any Javascript post processing to be applied.
- __project_status_definitions:__ Helper config for the aggregation of data from `limsdb`, defining what a
  sample should be marked as, depending on which workflows it has or has not been through.
- __review_thresholds.yaml:__ Config for rest_api.actions.automatic_review
- __schema.yaml:__ Passed to Eve as the schema/data validation layer. For more information, see the
  [Eve docs](http://python-eve.org/config.html#schema).


## database_versioning
Currently, this contains database migration scripts for instances where fields in the schema is altered, as opposed to
new fields being added.


## Docker
A dockerfile and template config are present in docker/ for building the Rest API component as a Docker image. To build
the image, navigate to this directory and run:

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
- __Tornado:__ Run Python on `bin/run_app.py` with the argument `reporting_app` or `rest_api`
- __Apache:__ Write a WSGI script for each app, for example:

```python
import sys
sys.path.append('/var/www/Reporting-App')
# set up config file env vars, etc/

import reporting_app
# set up logging, etc.

application = reporting_app.app
```
