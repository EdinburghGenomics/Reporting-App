
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


def add(*args):
    return {'$add': list(args)}


def multiply(*args):
    return {'$multiply': list(args)}


def divide(numerator, denominator, simple=False):
    div = {'$divide': [numerator, denominator]}
    if simple:
        return div
    else:
        return cond({'$eq': [denominator, 0]}, 0, div)


def percentage(numerator, denominator):
    return cond(
        eq(denominator, 0),
        0,
        multiply(divide(numerator, denominator, simple=True), 100)
    )


def and_(*args):
    return {'$and': list(args)}


def or_(*args):
    return {'$or': list(args)}


def lt(number, comparator):
    return {'$lt': [number, comparator]}


def gt(number, comparator):
    return {'$gt': [number, comparator]}


def eq(number, comparator):
    return {'$eq': [number, comparator]}


def cond(exp, if_true, if_false):
    return {'$cond': [exp, if_true, if_false]}


def if_else(*exprs, else_=None):
    """
    Translate a sequence of if/else statements into a nested aggregation query of $conds. E.g:
    if_else(
        {'$eq': ['$x', 0]},
        'X is 0',
        {'$eq': ['$x', 1]},
        'X is 1',
        else_='X is something else'
    )
    :param exprs: An alternating sequence of expression followed by a corresponding result (i.e., must be of
    even length!).
    :param else_: Final value to return if none of the if/elses are met.
    """
    assert len(exprs) % 2 == 0
    if exprs:
        exp, result = exprs[0:2]
        exprs = exprs[2:]
        return {'$cond': [exp, result, if_else(*exprs, else_=else_)]}
    else:
        return else_


def merge_analysis_driver_procs(id_field, projection=None):
    stages = [
        lookup('analysis_driver_procs', id_field, 'dataset_name'),
        {
            '$unwind': {
                'path': '$analysis_driver_procs',
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$sort': {id_field: -1, 'analysis_driver_procs._created': -1}
        }
    ]
    group = {
        '_id': '$' + id_field,
        'most_recent_proc': {'$first': '$analysis_driver_procs'}
    }
    for k in projection:
        group[k] = {'$first': '$' + k}
    stages.append({'$group': group})
    stages.append(
        lookup(
            'analysis_driver_stages',
            'most_recent_proc.proc_id',
            'analysis_driver_proc',
            'most_recent_proc.stages'
        )
    )
    return stages
