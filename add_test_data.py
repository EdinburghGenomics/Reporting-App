__author__ = 'mwham'
import requests
import random
from json import loads


def rand_percentage():
    return random.randint(0, 100)


def rand_float():
    return round(random.random(), 2)


def rand_int():
    return random.randint(1000, 4000)


def rand_barcode():
    ret_string = ''
    for x in range(8):
        ret_string += random.choice(['A', 'T', 'G', 'C'])
    return ret_string


def rand_file_path():
    parts = (random.choice(['this', 'that', 'other', 'another', 'more']) for _ in range(3))
    return '/'.join(parts)

def _around(base_num):
    return base_num * random.triangular(0.8, 1.2)



def sample_element(sample_id, run_element_ids):
    bam_file_reads = random.randint(8000, 10000)
    return {
        'library_id': 'lib_' + sample_id,
        'project': sample_id.split('_')[0],
        'sample_id': sample_id,
        'user_sample_id': 'user_' + sample_id,
        'bam_file_reads': bam_file_reads,
        'mapped_reads': bam_file_reads * _around(0.8),
        'properly_mapped_reads': bam_file_reads * _around(0.78),
        'duplicate_reads': bam_file_reads * _around(0.1),
        'median_coverage': rand_float(),
        'pc_callable': rand_percentage(),
        'run_elements': run_element_ids,
        'reviewed': random.choice(['not reviewed', 'pass', 'fail'])
    }


def run_element(run_id, lane, barcode, sample_id):
    run_element_id = '_'.join([run_id, lane, barcode])
    total_reads = random.randint(8000, 10000)
    bases_r1 = random.randint(1200000000, 1800000000)
    bases_r2 = random.randint(1200000000, 1800000000)
    return {
        'run_element_id': run_element_id,
        'run_id': run_id,
        'lane': lane,
        'barcode': barcode,
        'project': sample_id.split('_')[0],
        'library_id': 'lib_' + sample_id,
        'sample_id': sample_id,
        'total_reads': total_reads,
        'passing_filter_reads': total_reads * _around(0.79),
        'pc_reads_in_lane': rand_percentage(),
        'bases_r1': bases_r1,
        'q30_bases_r1': bases_r1 * _around(0.81),
        'bases_r2': bases_r2,
        'q30_bases_r2': bases_r2 * _around(0.81),
        'fastqc_report_r1': rand_file_path(),
        'fastqc_report_r2': rand_file_path(),
        'reviewed': random.choice(['not reviewed', 'pass', 'fail'])
    }


def unexpected_barcode(run_id, lane, barcode):
    return {
        'run_element_id': '_'.join([run_id, lane, barcode]),
        'run_id': run_id,
        'lane': lane,
        'barcode': barcode,
        'passing_filter_reads': rand_int(),
        'pc_reads_in_lane': rand_percentage()
    }


def run(run_id, lane_ids):
    return {
        'run_id': run_id,
        'lanes': lane_ids
    }


def lane(run_id, lane_number, run_element_ids):
    return {
        'lane_id': '_'.join((run_id, lane_number)),
        'run': run_id,
        'lane_number': lane_number,
        'run_elements': run_element_ids
    }


def project(name, sample_ids):
    return {
        'project_id': name,
        'samples': sample_ids
    }


ext_api = 'http://egclaritydev.mvm.ed.ac.uk:4999/api/0.1/'
int_api = 'http://localhost:4999/api/0.1/'
api_url = int_api


def push(resource, json):
    response = requests.post(api_url + resource, json=json)
    content = loads(response.content.decode('utf-8'))
    if content['_status'] != 'OK':
        print('oh noes! problem pushing to ' + resource)
        print(content)


def multi_push():
    run_ids_and_samples = (
        (('150723_test', '150724_test'), '10015AT_1_test'),
        (('150823_test', '150824_test'), '10015AT_2_test'),
        (('150923_test', '150924_test'), '10105AT_1_test')
    )

    for runs, sample_id in run_ids_and_samples:
        run_e_ids = []
        for run_id in runs:
            lane_ids = []
            for lane_number in ('1', '2', '3', '4', '5', '6', '7', '8'):
                b1 = rand_barcode()
                b2 = rand_barcode()
                while b2 == b1:
                    b2 = rand_barcode()

                run_es = [
                    run_element(run_id, lane_number, b1, sample_id),
                    run_element(run_id, lane_number, b2, sample_id)
                ]
                run_e_ids.extend([e['run_element_id'] for e in run_es])
                push('run_elements', json=run_es)

                l = lane(
                    run_id,
                    lane_number,
                    [
                        '_'.join((run_id, lane_number, b1)),
                        '_'.join((run_id, lane_number, b2))
                    ]
                )
                push('lanes', json=l)
                lane_ids.append(l['lane_id'])
            r = run(run_id, lane_ids)
            push('runs', json=r)

        s = sample_element(sample_id, run_e_ids)
        push('samples', json=s)

    p1 = project('10015AT', ['10015AT_1_test', '10015AT_2_test'])
    p2 = project('10105AT', ['10105AT_1_test'])
    push('projects', json=[p1, p2])


if __name__ == '__main__':
    # r = run_element('another', '9', 'run_element', '10015AT_test', '10015AT_test_1')
    # r['run_element'] = ['another_9_run_element', '150723_test_1_TTGGGGTC']
    #
    # push('run_elements', r)
    multi_push()
