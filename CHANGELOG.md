Changelog for Reporting-App
===========================

0.12.1
------
- Add Repeat status in sample/plate/project status

0.12
-----
 - Add abbility to create a Docker image of the reporting with sensible default 
 - Fix sample status definition 
 
0.11.2
------
 - Add an analysis_driver_proc to the project end point
 - Create run_status end point that queries the LIMS
 - Create run status view

0.11.1
------
### Rest API:
 * Add sample_status endpoint to the REST API
 * Simplify code for project/plate/sample status

### Reporting 
 * Make all titles collapse their respective section
 * Add section showing sample history in each sample section

0.11
----
 - Add stage end point to the REST API which used to be under analysis_driver_procs


0.9.2
-----
 - This release add a chart page that contains graphs summarising yield and number of sample per week/month.
 - It also add a fix for random error due to login token

0.9.1
-----
 - This fixes an unpredictable 500 Internal Server Error, as well as a bug where samples with no genotype data were reported as 'Match'. Coverage percentiles have also been added to the schema.

0.9
----
 - This version adds flask_login authentication, and the ability to run on Apache via mod_wsgi. The Rest API can be authenticated by username/password or by a login token stored as a cookie when the user signs into the Reporting App. There is a configurable timeout for login sessions. If an unauthenticated user tries to navigate to, e.g, /projects/<project>, they will be redirected to login. Upon successful login, the user will then be allowed to proceed to /projects/<project>.
 - This version includes a config change - the 'default' domain has been removed, so 'reporting_app' and 'rest_app' are now top-level
 - There may be incompatibilities with sqlite3 when running on Werkzeug
