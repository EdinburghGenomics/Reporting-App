__author__ = 'mwham'
import argparse
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
        'project': sample_id.split('_sample')[0],
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


def run_element(run_id, lane_nb, barcode, sample_id, incomplete=False):
    run_element_id = '_'.join([run_id, lane_nb, barcode])
    total_reads = random.randint(8000, 10000)
    bases_r1 = random.randint(1200000000, 1800000000)
    bases_r2 = random.randint(1200000000, 1800000000)
    if incomplete:
        return {
            'run_element_id': run_element_id,
            'run_id': run_id,
            'lane': lane_nb,
            'barcode': barcode,
            'project': sample_id.split('_')[0],
            'library_id': 'lib_' + sample_id,
            'sample_id': sample_id
        }
    else:
        return {
            'run_element_id': run_element_id,
            'run_id': run_id,
            'lane': lane_nb,
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


def unexpected_barcode(run_id, lane_nb, barcode):
    return {
        'run_element_id': '_'.join([run_id, lane_nb, barcode]),
        'run_id': run_id,
        'lane': lane_nb,
        'barcode': barcode,
        'passing_filter_reads': rand_int(),
        'pc_reads_in_lane': rand_percentage()
    }


def run(run_id, nlanes):
    return {
        'run_id': run_id,
        'number_of_lanes': nlanes
    }


def lane(run_id, lane_number, run_element_ids):
    return {
        'lane_id': '_'.join((run_id, lane_number)),
        'run_id': run_id,
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


class RESTError(Exception):
    pass


def push(resource, json):
    response = requests.post(api_url + resource, json=json)
    content = loads(response.content.decode('utf-8'))
    if content['_status'] != 'OK':
        raise RESTError('oh noes! problem pushing to ' + resource + '\n' + str(json) + '\n' + str(content))


def multi_push(run_ids_and_samples, elements_per_run=6, lanes_per_run=8):
    runs = []
    projects = []

    for project_id, run_ids in run_ids_and_samples:
        r_e_ids = []
        for run_id in run_ids:
            print(run_id)
            lanes = []

            for lane_number in (range(lanes_per_run)):
                lane_number = str(lane_number + 1)
                run_elements = []
                barcodes = []
                _sample_id = project_id + '_sample_' + lane_number

                for e in range(elements_per_run):
                    b = rand_barcode()
                    while b in barcodes:
                        b = rand_barcode()

                    r_e = run_element(run_id, lane_number, b, _sample_id, incomplete=random.choice([True, False]))
                    run_elements.append(r_e)

                l = lane(
                    run_id,
                    lane_number,
                    [e['run_element_id'] for e in run_elements]
                )
                lanes.append(l)

                r_e_ids.extend([e['run_element_id'] for e in run_elements])
                push('run_elements', json=run_elements)

            r = run(run_id, len(lanes))
            runs.append(r)
            push('lanes', json=lanes)

        samples = []
        for s in range(lanes_per_run):
            s = str(s + 1)
            sample_id = project_id + '_sample_' + s

            s = sample_element(sample_id, r_e_ids)
            samples.append(s)

        p = project(project_id, [e['sample_id'] for e in samples])
        projects.append(p)
        push('samples', json=samples)

    push('runs', json=runs)
    push('projects', json=projects)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--nruns', type=int, help='number of runs to add to the database')
    p.add_argument('--nsamples', type=int, help='number of samples to add. this must divide nruns cleanly.')
    args = p.parse_args()

    nruns = args.nruns
    nsamples = args.nsamples

    run_ids = ['run_' + str(x + 1) for x in range(nruns)]
    projects = ['test_project_' + str(y + 1) for y in range(nsamples)]

    assert nruns > nsamples, 'must have more runs than samples'
    runs_per_sample = int(nruns / nsamples)

    input_data = ((p, (run_ids.pop(0) for _ in range(runs_per_sample))) for p in projects)

    multi_push(input_data)
