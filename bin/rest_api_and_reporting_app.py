__author__ = 'mwham'
import sys
import os
import multiprocessing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import reporting_app
import rest_api


if __name__ == '__main__':
    for m in (rest_api, reporting_app):
        print('starting new process for ' + m.__name__)
        p = multiprocessing.Process(target=m.main)
        p.start()
