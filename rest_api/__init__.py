import os
import json
import eve
from eve_sqlalchemy import SQL
from eve_sqlalchemy.decorators import registerSchema
from eve_sqlalchemy.validation import ValidatorSQL
from rest_api import model

from config import rest_config as cfg


tables = (
    model.RunElement, model.UnexpectedBarcode, model.Sample, model.SequencingRun, model.Project,
    model.PipelineRun, model.PipelineStage
)
for table in tables:
    r = registerSchema(table.__tablename__)
    r(table)


sqlite_db = '/Users/mwham/workspace/sqlite/test'

settings = {
    'DOMAIN': {},

    'ID_FIELD': 'id',
    'VALIDATE_FILTERS': True,
    'ITEMS': 'data',

    'XML': False,

    'PAGINATION': True,
    'PAGINATION_LIMIT': 100000,

    'X_DOMAINS': cfg['x_domains'],

    'URL_PREFIX': 'api',
    'API_VERSION': '0.1',

    'RESOURCE_METHODS': ['GET', 'POST', 'DELETE'],
    'ITEM_METHODS': ['GET', 'PUT', 'PATCH', 'DELETE'],

    # 'CACHE_CONTROL': 'max-age=20',
    # 'CACHE_EXPIRES': 20,

    'DATE_FORMAT': '%d_%m_%Y_%H:%M:%S',

    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + sqlite_db,
    # 'SQLALCHEMY_BINDS',
    # 'SQLALCHEMY_NATIVE_UNICODE',
    # 'SQLALCHEMY_ECHO',
    # 'SQLALCHEMY_RECORD_QUERIES',
    # 'SQLALCHEMY_POOL_SIZE',
    # 'SQLALCHEMY_POOL_TIMEOUT',
    # 'SQLALCHEMY_POOL_RECYCLE',
    # 'SQLALCHEMY_MAX_OVERFLOW',
    # 'SQLALCHEMY_COMMIT_ON_TEARDOWN'
}

for table in tables:
    n = table.__tablename__
    s = table._eve_schema[n]
    settings['DOMAIN'][n] = s
    settings['DOMAIN'][n].update(
        {'item_title': table.item_title, 'item_lookup_field': 'id'}
    )
    # print(n)
    # print(s)
    # for f in table.aggregated_fields:
    #     settings['DOMAIN'][n]['schema'].update(
    #         {f: {'unique': False, 'type': 'string', 'nullable': True, 'required': False}}
    #     )


def format_json(resource, request, response):
    response.data = json.dumps(json.loads(response.data.decode('utf-8')), indent=4).encode()


if __name__ == '__main__':
    if os.path.isfile(sqlite_db):
        os.remove(sqlite_db)
    app = eve.Eve(settings=settings, data=SQL, validator=ValidatorSQL)

    from sqlalchemy import create_engine

    db = app.data.driver
    db.engine.echo = 'debug'
    model.Base.metadata.bind = db.engine
    db.Model = model.Base
    db.create_all()

    app.on_post_GET += format_json
    app.run(port=4999, debug=True, use_reloader=False)
'''
query = db.session.query(Sample).filter_by(sample_id='sample_1').all()
print(query)

s = query[0]
print(s.run_elements)
'''
