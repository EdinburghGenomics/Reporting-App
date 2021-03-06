Changelog for Reporting-App
===========================


0.24 (unreleased)
-----------------

- Nothing changed yet.


0.23 (2019-10-29)
-----------------

- Bioinformatics activity trending - new page showing number of concurrent pipeline processes over time
- Samplesheet information is now available via the endpoint `lims/run_status`
- Adds the ability to load data into the LIMS database from a YAML file when using a SQLite back end
- Makes the library plate view generic and adds the ability to view genotyping plates. Adds a summary table to both these views
- Adds library information to sample and project pages


0.22 (2019-07-09)
-----------------

- New sequencing trending and turnaround graphs
- New library prep QC view and database queries
- Coloured project status by staleness
- New page for samples not processing
- 'gender' database keys renamed to 'sex'
- Updated EGCG-Core to v0.11


0.21.1 (2019-06-12)
-------------------

- Update to schema for rapid processing and GATK4 pipelines
- Add new LIMS step in dsample status definition to transition to Sample QC/Library Prep/Library Queue


0.21 (2019-04-29)
-----------------

- New date filters in project/sample status endpoints
- Less misleading column names, tweaked show-hide defaults
- Pipeline data in project table
- Pipeline/genome data in sample table
- Removed run top-level autoreview
- Removed server_side and database_side aggregation
- Not showing samples as Invoicing if they're removed


0.20.2 (2019-02-20)
-------------------

- Removal of required_yield_q30 from automatic sample review
- GC bias storage metrics
- Empty list formatting bug fix


0.20.1 (2018-11-30)
-------------------

- Fix bug in the display single sample cells in project status page

0.20 (2018-11-30)
-----------------

- New Species and Genome Page describing the currently supported species and the yield values
- In Automatic Run review: compound formula now use read duplicates and 96G
- Sample finished date now points to first finished status rather than the last
- Nb samples received added back to Project status lines
 
 0.19.1 (2018-09-18)
-------------------

- Bug fix in Automatic Sample Review where yield in gb were compared with required yield in base


0.19 (2018-09-17)
-----------------

- Added expected yield/coverage columns to project and plate status tables
- Added Data Release Trigger to `DELIVERY` status
- New review thresholds
    - Overall run: total yield, %Q30, %Q30 R1/2
    - Lane: %Q30 R1/2, adaptors and duplicates
    - Adding `formula` logic
- Added commit hash to dev instances
- Highlighting samples which have different usable data from processed data
- Adding usable run elements to sample aggregation
- Adding required yield and species to Lims queries


0.18.2 (2018-06-01)
-------------------

- Add field for storing phix and display it on run/lane/run_elements
- Fix status definition for genotyping and finished 
- Code refactor 


0.18.1 (2018-04-30)
-------------------

- fix project status URL bug


0.18 (2018-04-27)
-----------------

- Allow multiple projects to be viewed on one page
- Show open and closed projects
- Fix bug in lane review


0.17.1 (2018-02-22)
-------------------

- Fix process in progress in sample's process list
- Add other insert type in schema to record non standard insert and fix median insert size
- Fix sample status remove by adding "Request Repeat"
- Fix schema to support pipeline resume
- Add interop metrics to the lane end point

0.17 (2018-01-17)
-----------------

- add tests for limsdb
- get coverage values from rest API/LIMS rather than from hardcoded values
- Use aggregated data


0.16 (2017-11-27)
-----------------

- Added on-insert data aggregation via Eve database hooks
- Added a Python 3.6 build
- Removed Werkzeug server option
- Updated to Eve 0.7.4 and PyMongo 3.5.1
- Remove sample expected yield and add required yield/yieldq30/coverage
- Fix date started in sample status


0.15.2 (2017-11-08)
-------------------

- Fix coloring issue that caused some rows to use the wrong threshold


0.15.1 (2017-11-08)
-------------------

- Fix thresholds for Automatic review actions and coloring in the web app to match SOPs
- Add schema information to support mapping metrics in run_elements
- Fix automatic sample review (Server error) 

0.15 (2017-09-06)
-----------------

- Added initiation of LIMS-based run/sample review
    - modal popup to initiate review of selected rows of a datatable
    - sends a POST entry to new `actions` endpoint
      - starts a LIMS step and sends back the step url
- Automatic run/sample review
    - as from EGCG-Project-Management
    - applies metric-based review and pushes results directly back to the database 
- Removed `/runs/recentlims` page
- Added cst_date to `/lims/status/run_status`
- Added `Finish Processing` to project status
- Fixed setup in Docker image entrypoint
- Added recent, current_year and year_to_date run views
- New datatable columns: `coverage_5X`, `cst_date`, `mean_coverage` (pointing to coverage.mean)
- New schema entries:
    - run_elements: `useable_reviewer`
    - projects: `sample_pipeline` (stores which pipeline version to use for a sample in a project)
    - samples: `useable_reviewer`, `files_delivered.size`, `files_downloaded.size`
    - analysis_driver_procs: `pipeline_used` (stores the pipeline version run on a dataset)
    - `actions` endpoint
    - records actions performed on the REST API
- Schema fixes:
    - fixed data type of `useable_comments`
- Added EGCG-Core and PyClarity-Lims as requirements


0.14.3 (2017-06-28)
-------------------

- Added 2D barcode field to sample view
- Made tiles_filtered, trim_r1 and trim_r2 nullable
- Added files_delivered and files_downloaded to sample schema
- Added data_source to analysis_driver_proc schema


0.14.2 (2017-05-24)
-------------------

- Add Cleaned yield/%Q30 in many pages along with colouring of row that described filtered runs


0.14.1 (2017-05-16)
-------------------

- Fix queries to sample info and sample status with no match statement.


0.14 (2017-05-16)
-----------------

- Add unitest to javascript code through Qunit
- Reorganise the Samples and Runs pages to remove the one nobody was using


0.13.2 (2017-05-02)
-------------------

- Add new lims end point showing sample information from udfs
- Add multiple columns in sample report
- Fix FluidX samples status 


0.13.1 (2017-04-18)
-------------------

- Fix sample page


0.13 (2017-04-18)
-----------------
 - Add repeat status in sample/plate/project status
 - Enable merging of multiple rest API queries in datatables: Use this to get the LIMS status into bioinformatics report
 - Stage timeline has been refactored and now shows exit status
  
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
