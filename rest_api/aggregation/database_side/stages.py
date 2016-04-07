
def lookup(foreign_resource, local_field, foreign_field=None, embed_as=None):
    if foreign_field is None:
        foreign_field = local_field

    if embed_as is None:
        embed_as = foreign_resource

    return {
        '$lookup': {
            'from': foreign_resource,
            'localField': local_field,
            'foreignField': foreign_field,
            'as': embed_as
        }
    }


def order(sort_col):
    if sort_col.startswith('-'):
        sort_expr = {sort_col.lstrip('-'): -1}
    else:
        sort_expr = {sort_col: 1}
    return {'$sort': sort_expr}


def paginator(sort_col, page_number, page_size):
    pipeline = [order(sort_col)]
    skip = int(page_size) * (int(page_number) - 1)
    if skip:
        pipeline.append({'$skip': skip})
    pipeline.append({'$limit': int(page_size)})

    return pipeline


def add(*args):
    return {'$add': list(args)}


def divide(numerator, denominator):
    return {
        '$cond': {
            'if': {'$eq': [denominator, 0]},
            'then': 0,
            'else': {'$divide': [numerator, denominator]}
        }
    }


def percentage(numerator, denominator):
    return {
        '$cond': {
            'if': {'$eq': [denominator, 0]},
            'then': 0,
            'else': {'$multiply': [{'$divide': [numerator, denominator]}, 100]}
        }
    }
