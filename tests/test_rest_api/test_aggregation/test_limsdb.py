from unittest.case import TestCase

from datetime import datetime

from rest_api.limsdb.queries.project_status import Sample
from tests.test_rest_api.test_aggregation import TestAggregation, FakeRequest
from unittest.mock import Mock, patch
from rest_api.aggregation import database_side
from rest_api.aggregation.database_side import stages as s


class SampleTest(TestCase):

    def setUp(self):
        self.sample1 = Sample()
        self.sample1.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'))
        self.sample1.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'))

        self.sample2 = Sample()
        self.sample2.add_completed_process('Change Freezer Location EG 2.0',
                                           datetime.strptime('2016-11-25 09:22:13.824000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Finance - Invoice Processed',
                                           datetime.strptime('2016-09-28 12:42:44.890000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Finance - Invoice To Be Sent',
                                           datetime.strptime('2016-09-28 12:40:31.600000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Data Release EG 1.0',
                                           datetime.strptime('2016-07-12 14:16:04.591000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-06-13 14:44:39.039000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Cluster Flowcell',
                                           datetime.strptime('2016-06-13 10:44:09.024000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make CST',
                                           datetime.strptime('2016-06-13 10:18:13.962000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Create Production CST Batch',
                                           datetime.strptime('2016-06-13 09:23:46.341000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Change Lanes Remaining and PDP Uses',
                                           datetime.strptime('2016-06-09 09:46:59.466000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make NTP',
                                           datetime.strptime('2016-06-08 15:50:03.689000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-06-07 09:00:10.262000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('SEMI-AUTOMATED - Make and Read qPCR Quant',
                                           datetime.strptime('2016-06-06 14:47:00.301000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('SEMI-AUTOMATED - Make and Read qPCR Quant',
                                           datetime.strptime('2016-05-31 12:11:03.826000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Clean Up ALP',
                                           datetime.strptime('2016-05-27 11:26:02.415000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Incubate 2 ALP',
                                           datetime.strptime('2016-05-27 11:16:41.854000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Read and Eval SSQC',
                                           datetime.strptime('2016-05-27 10:54:34.456000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Add LIG',
                                           datetime.strptime('2016-05-27 10:39:18.885000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Incubate 1 ALP',
                                           datetime.strptime('2016-05-27 10:24:29.272000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Add ATL',
                                           datetime.strptime('2016-05-27 09:33:51.116000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Size Select IMP',
                                           datetime.strptime('2016-05-26 13:57:37.960000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Incubate IMP',
                                           datetime.strptime('2016-05-26 13:46:51.175000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make IMP',
                                           datetime.strptime('2016-05-26 12:58:25.148000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Fragment DNA (Covaris)',
                                           datetime.strptime('2016-05-26 12:48:35.054000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make Normalized CFP',
                                           datetime.strptime('2016-05-26 10:43:34.839000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Create CFP Batch',
                                           datetime.strptime('2016-05-26 10:24:28.831000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-04-22 14:41:26.197000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-04-22 10:38:00.764000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Cluster Flowcell',
                                           datetime.strptime('2016-04-21 14:58:56.492000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make CST',
                                           datetime.strptime('2016-04-21 14:32:01.102000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Create Production CST Batch',
                                           datetime.strptime('2016-04-21 10:19:11.782000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Change Lanes Remaining and PDP Uses',
                                           datetime.strptime('2016-04-21 09:50:24.245000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make NTP',
                                           datetime.strptime('2016-04-20 15:02:38.086000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-04-20 12:14:53.686000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('SEMI-AUTOMATED - Make and Read qPCR Quant',
                                           datetime.strptime('2016-04-20 11:54:03.606000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Genotyping Data Received EG 1.0',
                                           datetime.strptime('2016-04-15 10:56:30.074000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Genotyping Sample Dispatched EG 1.0',
                                           datetime.strptime('2016-04-13 15:14:48.583000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Genotyping Plate Preparation EG 1.0',
                                           datetime.strptime('2016-03-23 10:05:40.967000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-02-26 10:52:06.619000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-02-25 15:59:20.846000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Cluster Flowcell',
                                           datetime.strptime('2016-02-25 11:56:13.517000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make Pooled CST',
                                           datetime.strptime('2016-02-25 11:22:35.761000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Create Pooling CST Batch',
                                           datetime.strptime('2016-02-25 11:08:27.617000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make PDP',
                                           datetime.strptime('2016-02-24 14:57:09.741000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Create PDP Pool',
                                           datetime.strptime('2016-02-24 14:44:46.273000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make PDP',
                                           datetime.strptime('2016-02-24 13:54:23.926000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Update Yields (Gb)',
                                           datetime.strptime('2016-02-24 13:46:12.976000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Create PDP Pool',
                                           datetime.strptime('2016-02-24 13:33:50.717000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make DTP',
                                           datetime.strptime('2016-02-24 12:18:08.450000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make NTP',
                                           datetime.strptime('2016-02-24 11:58:46.609000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-02-23 15:53:12.996000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('SEMI-AUTOMATED - Make and Read qPCR Quant',
                                           datetime.strptime('2016-02-23 14:01:07.193000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Clean Up ALP',
                                           datetime.strptime('2016-02-23 11:01:15.159000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Incubate 2 ALP',
                                           datetime.strptime('2016-02-23 10:47:59.306000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Add LIG',
                                           datetime.strptime('2016-02-23 10:17:29.014000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Incubate 1 ALP',
                                           datetime.strptime('2016-02-23 10:04:14.076000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Add ATL',
                                           datetime.strptime('2016-02-23 09:09:47.493000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Read and Eval SSQC',
                                           datetime.strptime('2016-02-18 09:31:00.226000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Size Select IMP',
                                           datetime.strptime('2016-02-17 14:51:44.645000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Incubate IMP',
                                           datetime.strptime('2016-02-17 14:38:34.795000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make IMP',
                                           datetime.strptime('2016-02-17 13:42:11.759000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Fragment DNA (Covaris)',
                                           datetime.strptime('2016-02-17 13:35:26.987000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('AUTOMATED - Make Normalized CFP',
                                           datetime.strptime('2016-02-17 12:08:38.541000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Create CFP Batch',
                                           datetime.strptime('2016-02-17 11:58:55.479000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Eval Project Quant',
                                           datetime.strptime('2016-02-17 11:47:39.127000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('SEMI-AUTOMATED - Make DNA Quant & Eval Standard Quant',
                                           datetime.strptime('2016-02-17 10:52:32.144000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('SEMI-AUTOMATED - Make DNA Quant & Eval Standard Quant',
                                           datetime.strptime('2016-02-17 09:30:48.637000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Visual QC',
                                           datetime.strptime('2016-02-17 08:58:11.435000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Sample Placement EG 1.0',
                                           datetime.strptime('2016-02-16 16:32:00.123000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Spectramax Picogreen EG 3.0',
                                           datetime.strptime('2016-02-02 15:04:08.200000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Courier Number for New Plate Dispatch',
                                           datetime.strptime('2016-01-27 09:36:05.797000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Receive Sample 4.0',
                                           datetime.strptime('2016-01-26 14:55:59.099000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Bartender label generation EG 3.1',
                                           datetime.strptime('2016-01-22 08:31:34.125000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Plate Recipient Details',
                                           datetime.strptime('2016-01-20 11:37:25.686000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample2.add_completed_process('Upload Gel Images EG 1.0',
                                           datetime.strptime('2016-01-20 11:27:58.501000', '%Y-%m-%d %H:%M:%S.%f'))

        self.sample3 = Sample()
        self.sample3.add_completed_process('Finance - Invoice Processed',
                                           datetime.strptime('2016-09-28 12:42:44.890000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Finance - Invoice To Be Sent',
                                           datetime.strptime('2016-09-28 12:40:31.600000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Data Release EG 1.0',
                                           datetime.strptime('2016-07-12 14:16:04.591000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-06-13 14:44:39.039000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Create Production CST Batch',
                                           datetime.strptime('2016-06-13 09:23:46.341000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Make NTP',
                                           datetime.strptime('2016-06-08 15:50:03.689000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-06-07 09:00:10.262000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Create CFP Batch',
                                           datetime.strptime('2016-05-26 10:24:28.831000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-04-22 14:41:26.197000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-04-22 10:38:00.764000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Create Production CST Batch',
                                           datetime.strptime('2016-04-21 10:19:11.782000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-04-20 12:14:53.686000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-02-26 10:52:06.619000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-02-25 15:59:20.846000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Create Pooling CST Batch',
                                           datetime.strptime('2016-02-25 11:08:27.617000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Create PDP Pool',
                                           datetime.strptime('2016-02-24 14:44:46.273000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Make PDP',
                                           datetime.strptime('2016-02-24 13:54:23.926000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Update Yields (Gb)',
                                           datetime.strptime('2016-02-24 13:46:12.976000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Create PDP Pool',
                                           datetime.strptime('2016-02-24 13:33:50.717000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Make DTP',
                                           datetime.strptime('2016-02-24 12:18:08.450000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Make NTP',
                                           datetime.strptime('2016-02-24 11:58:46.609000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-02-23 15:53:12.996000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Clean Up ALP',
                                           datetime.strptime('2016-02-23 11:01:15.159000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('AUTOMATED - Size Select IMP',
                                           datetime.strptime('2016-02-17 14:51:44.645000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Visual QC',
                                           datetime.strptime('2016-02-17 08:58:11.435000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Sample Placement EG 1.0',
                                           datetime.strptime('2016-02-16 16:32:00.123000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Spectramax Picogreen EG 3.0',
                                           datetime.strptime('2016-02-02 15:04:08.200000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Receive Sample 4.0',
                                           datetime.strptime('2016-01-26 14:55:59.099000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample3.add_completed_process('Upload Gel Images EG 1.0',
                                           datetime.strptime('2016-01-20 11:27:58.501000', '%Y-%m-%d %H:%M:%S.%f'))

        self.sample4 = Sample()
        self.sample4.add_queue_location('Create Production CST Batch',
                                        datetime.strptime('2016-06-14 14:44:39.039000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Sequence',
                                   datetime.strptime('2016-06-13 14:44:39.039000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Create Production CST Batch',
                                           datetime.strptime('2016-06-13 09:23:46.341000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Make NTP',
                                           datetime.strptime('2016-06-08 15:50:03.689000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-06-07 09:00:10.262000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Create CFP Batch',
                                           datetime.strptime('2016-05-26 10:24:28.831000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-04-22 14:41:26.197000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-04-22 10:38:00.764000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Create Production CST Batch',
                                           datetime.strptime('2016-04-21 10:19:11.782000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-04-20 12:14:53.686000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-02-26 10:52:06.619000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Sequence',
                                           datetime.strptime('2016-02-25 15:59:20.846000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Create Pooling CST Batch',
                                           datetime.strptime('2016-02-25 11:08:27.617000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Create PDP Pool',
                                           datetime.strptime('2016-02-24 14:44:46.273000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Make PDP',
                                           datetime.strptime('2016-02-24 13:54:23.926000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Update Yields (Gb)',
                                           datetime.strptime('2016-02-24 13:46:12.976000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Create PDP Pool',
                                           datetime.strptime('2016-02-24 13:33:50.717000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Make DTP',
                                           datetime.strptime('2016-02-24 12:18:08.450000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Make NTP',
                                           datetime.strptime('2016-02-24 11:58:46.609000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Eval qPCR Quant',
                                           datetime.strptime('2016-02-23 15:53:12.996000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Clean Up ALP',
                                           datetime.strptime('2016-02-23 11:01:15.159000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('AUTOMATED - Size Select IMP',
                                           datetime.strptime('2016-02-17 14:51:44.645000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Visual QC',
                                           datetime.strptime('2016-02-17 08:58:11.435000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Sample Placement EG 1.0',
                                           datetime.strptime('2016-02-16 16:32:00.123000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Spectramax Picogreen EG 3.0',
                                           datetime.strptime('2016-02-02 15:04:08.200000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Receive Sample 4.0',
                                           datetime.strptime('2016-01-26 14:55:59.099000', '%Y-%m-%d %H:%M:%S.%f'))
        self.sample4.add_completed_process('Upload Gel Images EG 1.0',
                                           datetime.strptime('2016-01-20 11:27:58.501000', '%Y-%m-%d %H:%M:%S.%f'))

    def tearDown(self):
        pass

    def test_status(self):
        assert self.sample1.status == 'sample_qc'


    def test_all_status(self):
        from pprint import pprint
        pprint(self.sample4.all_status())