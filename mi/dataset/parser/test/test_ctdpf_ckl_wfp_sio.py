#!/usr/bin/env python

"""
@package mi.dataset.parser.test.test_ctdpf_ckl_wfp_sio
@file marine-integrations/mi/dataset/parser/test/test_ctdpf_ckl_wfp_sio.py
@author cgoodrich
@brief Test code for a ctdpf_ckl_wfp_sio data parser
"""
import os
import struct
import ntplib
from StringIO import StringIO

from nose.plugins.attrib import attr

from mi.core.log import get_logger
log = get_logger()
from mi.idk.config import Config

from mi.dataset.test.test_parser import ParserUnitTestCase
from mi.dataset.dataset_parser import DataSetDriverConfigKeys
from mi.dataset.parser.ctdpf_ckl_wfp_sio import CtdpfCklWfpSioParser
from mi.dataset.parser.ctdpf_ckl_wfp_sio import CtdpfCklWfpSioDataParticle,\
    CtdpfCklWfpSioMetadataParticle

# Data stream which contains a decimation factor
TEST_DATA_wdf = b'\x01\x57\x43\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                 '\x30\x30\x33\x36\x48\x35\x31\x46\x32\x35\x42' + \
                 '\x44\x43\x5f\x31\x34\x5f\x37\x36\x33\x44\x02' + \
                 '\x00\x1a\x88\x03\xe3\x3b\x00\x03\xeb\x0a\xc8' + \
                 '\x00\x1a\x8c\x03\xe2\xc0\x00\x03\xeb\x0a\x81' + \
                 '\x00\x1a\x90\x03\xe1\x5b\x00\x03\xeb\x0a\x65' + \
                 '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' + \
                 '\x52\x4e\x75\x82\x52\x4e\x76\x9a\x00\x0A\x03'

# Data stream which does not contain a decimation factor
TEST_DATA_ndf = b'\x01\x57\x43\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                 '\x30\x30\x33\x34\x48\x35\x31\x46\x32\x35\x42' + \
                 '\x44\x43\x5f\x31\x34\x5f\x39\x41\x32\x38\x02' + \
                 '\x00\x1a\x88\x03\xe3\x3b\x00\x03\xeb\x0a\xc8' + \
                 '\x00\x1a\x8c\x03\xe2\xc0\x00\x03\xeb\x0a\x81' + \
                 '\x00\x1a\x90\x03\xe1\x5b\x00\x03\xeb\x0a\x65' + \
                 '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' + \
                 '\x52\x4e\x75\x82\x52\x4e\x76\x9a\x03'

# Data stream which does the wrong header (WA not WC)
TEST_DATA_whb = b'\x01\x57\x41\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                 '\x30\x30\x33\x34\x48\x35\x31\x46\x32\x35\x42' + \
                 '\x44\x43\x5f\x31\x34\x5f\x39\x41\x32\x38\x02' + \
                 '\x00\x1a\x88\x03\xe3\x3b\x00\x03\xeb\x0a\xc8' + \
                 '\x00\x1a\x8c\x03\xe2\xc0\x00\x03\xeb\x0a\x81' + \
                 '\x00\x1a\x90\x03\xe1\x5b\x00\x03\xeb\x0a\x65' + \
                 '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' + \
                 '\x52\x4e\x75\x82\x52\x4e\x76\x9a\x03'

# Data stream which does not have enough timestamp bytes
TEST_DATA_bts = b'\x01\x57\x43\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                 '\x30\x30\x33\x33\x48\x35\x31\x46\x32\x35\x42' + \
                 '\x44\x43\x5f\x31\x34\x5f\x31\x45\x36\x33\x02' + \
                 '\x00\x1a\x88\x03\xe3\x3b\x00\x03\xeb\x0a\xc8' + \
                 '\x00\x1a\x8c\x03\xe2\xc0\x00\x03\xeb\x0a\x81' + \
                 '\x00\x1a\x90\x03\xe1\x5b\x00\x03\xeb\x0a\x65' + \
                 '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' + \
                 '\x52\x4e\x75\x82\x52\x4e\x76\x03'

# Data stream which has no timestamp bytes
TEST_DATA_nts = b'\x01\x57\x43\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                 '\x30\x30\x32\x43\x48\x35\x31\x46\x32\x35\x42' + \
                 '\x44\x43\x5f\x31\x34\x5f\x33\x31\x39\x37\x02' + \
                 '\x00\x1a\x88\x03\xe3\x3b\x00\x03\xeb\x0a\xc8' + \
                 '\x00\x1a\x8c\x03\xe2\xc0\x00\x03\xeb\x0a\x81' + \
                 '\x00\x1a\x90\x03\xe1\x5b\x00\x03\xeb\x0a\x65' + \
                 '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' + \
                 '\x03'

# Data stream which has a bad end-of-profile marker
TEST_DATA_beop = b'\x01\x57\x43\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                  '\x30\x30\x33\x34\x48\x35\x31\x46\x32\x35\x42' + \
                  '\x44\x43\x5f\x31\x34\x5f\x45\x34\x43\x32\x02' + \
                  '\x00\x1a\x88\x03\xe3\x3b\x00\x03\xeb\x0a\xc8' + \
                  '\x00\x1a\x8c\x03\xe2\xc0\x00\x03\xeb\x0a\x81' + \
                  '\x00\x1a\x90\x03\xe1\x5b\x00\x03\xeb\x0a\x65' + \
                  '\xff\xff\xff\xff\xff\xfe\xff\xff\xff\xff\xff' + \
                  '\x52\x4e\x75\x82\x52\x4e\x76\x9a\x03'

# Data stream which has no end-of-profile marker
TEST_DATA_neop = b'\x01\x57\x43\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                  '\x30\x30\x33\x34\x48\x35\x31\x46\x32\x35\x42' + \
                  '\x44\x43\x5f\x31\x34\x5f\x39\x34\x37\x41\x02' + \
                  '\x00\x1a\x88\x03\xe3\x3b\x00\x03\xeb\x0a\xc8' + \
                  '\x00\x1a\x8c\x03\xe2\xc0\x00\x03\xeb\x0a\x81' + \
                  '\x00\x1a\x90\x03\xe1\x5b\x00\x03\xeb\x0a\x65' + \
                  '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
                  '\x52\x4e\x75\x82\x52\x4e\x76\x9a\x03'

# Data stream which has no data records
TEST_DATA_ndr = b'\x01\x57\x43\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                 '\x30\x30\x31\x33\x48\x35\x31\x46\x32\x35\x42' + \
                 '\x44\x43\x5f\x31\x34\x5f\x32\x42\x33\x30\x02' + \
                 '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' + \
                 '\x52\x4e\x75\x82\x52\x4e\x76\x9a\x03'

# Data stream which is way too short (no data, bad eop)
TEST_DATA_wts = b'\x01\x57\x43\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                 '\x30\x30\x31\x31\x48\x35\x31\x46\x32\x35\x42' + \
                 '\x44\x43\x5f\x31\x34\x5f\x31\x43\x44\x33\x02' + \
                 '\xff\xff\xff\xff\xff\xff\xff\xff\xff\x52\x4e' + \
                 '\x75\x82\x52\x4e\x76\x9a\x03'

# Data stream which contains the wrong header
TEST_DATA_wwh = b'\x01\x57\x41\x31\x32\x33\x36\x38\x32\x30\x5f' + \
                 '\x30\x30\x33\x34\x48\x35\x31\x46\x32\x35\x42' + \
                 '\x44\x43\x5f\x31\x34\x5f\x39\x41\x32\x38\x02' + \
                 '\x00\x1a\x88\x03\xe3\x3b\x00\x03\xeb\x0a\xc8' + \
                 '\x00\x1a\x8c\x03\xe2\xc0\x00\x03\xeb\x0a\x81' + \
                 '\x00\x1a\x90\x03\xe1\x5b\x00\x03\xeb\x0a\x65' + \
                 '\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' + \
                 '\x52\x4e\x75\x82\x52\x4e\x76\x9a\x03'

# Actual data contained in the data streams above
EXPECTED_TIME_STAMP = (1380873602, 1380873882, 3.0, 10)
EXPECTED_TIME_STAMP_ndf = (1380873602, 1380873882, 3.0, 0)

EXPECTED_VALUES_1 = (6792, 254779, 1003)
EXPECTED_VALUES_2 = (6796, 254656, 1003)
EXPECTED_VALUES_3 = (6800, 254299, 1003)

RESOURCE_PATH = os.path.join(Config().base_dir(), 'mi',
                             'dataset', 'driver', 'ctdpf_ckl',
                             'wfp_sio', 'resource')


@attr('UNIT', group='mi')
class CtdpfCklWfpSioMuleParserUnitTestCase(ParserUnitTestCase):
    """
    ctdpf_ckl_wfp_sio_mule Parser unit test suite
    """

    def exception_callback(self, exception):
        """ Callback method to watch what comes in via the exception callback """
        self.exception_callback_value = exception

    def setUp(self):

        ParserUnitTestCase.setUp(self)

        self.config = {
            DataSetDriverConfigKeys.PARTICLE_MODULE: 'mi.dataset.parser.ctdpf_ckl_wfp_sio',
            DataSetDriverConfigKeys.PARTICLE_CLASS: ['CtdpfCklWfpSioDataParticle',
                                                     'CtdpfCklWfpSioMetadataParticle']
        }

        # Define test data particles and their associated timestamps which will be
        # compared with returned results
        timefields = struct.unpack('>II', '\x52\x4e\x75\x82\x52\x4e\x76\x9a')
        start_time = int(timefields[0])
        end_time = int(timefields[1])

        # As there are only three records in the test data, divide by 3.
        time_increment = float(end_time - start_time) / 3.0

        self.start_timestamp = self.calc_timestamp(start_time, time_increment, 0)
        self.particle_meta = CtdpfCklWfpSioMetadataParticle(EXPECTED_TIME_STAMP,
                                                            internal_timestamp=self.start_timestamp)
        self.particle_meta_ndf = CtdpfCklWfpSioMetadataParticle(EXPECTED_TIME_STAMP_ndf,
                                                                internal_timestamp=self.start_timestamp)
        self.particle_a = CtdpfCklWfpSioDataParticle(EXPECTED_VALUES_1,
                                                     internal_timestamp=self.start_timestamp)

        self.timestamp_2 = self.calc_timestamp(start_time, time_increment, 1)
        self.particle_b = CtdpfCklWfpSioDataParticle(EXPECTED_VALUES_2,
                                                     internal_timestamp=self.timestamp_2)

        timestamp_3 = self.calc_timestamp(start_time, time_increment, 2)
        self.particle_c = CtdpfCklWfpSioDataParticle(EXPECTED_VALUES_3,
                                                     internal_timestamp=timestamp_3)

    def calc_timestamp(self, start, increment, sample_idx):
        new_time = start + (increment * sample_idx)
        return float(ntplib.system_to_ntp_time(new_time))

    def assert_result(self, result, particle, ingested):
        self.assertEqual(result, [particle])
        self.assertEqual(self.file_ingested_value, ingested)
        self.assert_(isinstance(self.publish_callback_value, list))
        self.assertEqual(self.publish_callback_value[0], particle)

    def test_simple_with_decimation_factor(self):
        """
        Read test data. Should detect that there is a decimation factor in the data.
        Check that the data matches the expected results.
        """
        log.debug('CAG TEST: FILE HAS DECIMATION FACTOR')
        stream_handle = StringIO(TEST_DATA_wdf)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(4)

        self.assertEqual(result, [self.particle_meta,
                                  self.particle_a,
                                  self.particle_b,
                                  self.particle_c])
        log.debug('CAG TEST: DECIMATION FACTOR TEST PASSES')

    def test_simple_with_no_decimation_factor(self):
        """
        Read test data. Should detect that there is NO decimation factor in the data.
        Check that the data matches the expected results.
        """
        log.debug('CAG TEST: FILE HAS NO DECIMATION FACTOR')
        stream_handle = StringIO(TEST_DATA_ndf)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)

        # next get records
        result = parser.get_records(4)

        self.assertEqual(result, [self.particle_meta_ndf,
                                  self.particle_a,
                                  self.particle_b,
                                  self.particle_c])
        log.debug('CAG TEST: NO DECIMATION FACTOR TEST PASSES')

    def test_simple_with_incorrect_header(self):
        """
        Read test data. Should detect that the header is NOT for a WC SIO block
        Data stream should be rejected.
        """
        log.debug('CAG TEST: INCORRECT HEADER')
        stream_handle = StringIO(TEST_DATA_bts)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(4)
        if result:
            log.debug('CAG TEST: FAILED TO DETECT INCORRECT HEADER')
            self.fail()
        else:
            log.debug('CAG TEST: INCORRECT HEADER DETECTED')
            pass

    def test_simple_with_bad_time_stamp(self):
        """
        Read test data. Should detect that the data has a bad time stamp (only 7 bytes).
        Data stream should be rejected.
        """
        log.debug('CAG TEST: BAD TIME STAMP')
        stream_handle = StringIO(TEST_DATA_bts)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(4)
        if result:
            log.debug('CAG TEST: FAILED TO DETECT BAD TIME STAMP')
            self.fail()
        else:
            log.debug('CAG TEST: BAD TIME STAMP DETECTED')
            pass

    def test_simple_with_no_time_stamp(self):
        """
        Read test data. Should detect that the data is missing the time stamp.
        Data stream should be rejected.
        """
        log.debug('CAG TEST: NO TIME STAMP')
        stream_handle = StringIO(TEST_DATA_nts)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(4)
        if result:
            log.debug('CAG TEST: FAILED TO DETECT NO TIME STAMP')
            self.fail()
        else:
            log.debug('CAG TEST: NO TIME STAMP DETECTED')
            pass

    def test_simple_with_bad_eop(self):
        """
        Read test data. Should detect that the End of Profile (eop) is not all "F"s.
        Data stream should be rejected.
        """
        log.debug('CAG TEST: BAD END OF PROFILE')
        stream_handle = StringIO(TEST_DATA_beop)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(4)
        if result:
            log.debug('CAG TEST: FAILED TO DETECT BAD END OF PROFILE')
            self.fail()
        else:
            log.debug('CAG TEST: BAD END OF PROFILE DETECTED')
            pass

    def test_simple_with_no_eop(self):
        """
        Read test data. Should detect that the End of Profile (eop) is missing.
        Data stream should be rejected.
        """
        log.debug('CAG TEST: MISSING END OF PROFILE')
        stream_handle = StringIO(TEST_DATA_neop)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(4)
        if result:
            log.debug('CAG TEST: FAILED TO DETECT MISSING END OF PROFILE')
            self.fail()
        else:
            log.debug('CAG TEST: MISSING END OF PROFILE DETECTED')
            pass

    def test_simple_with_no_data_recs(self):
        """
        Read test data. Should detect that there is no data between the header and footer.
        Data out should be a metadata particle only
        """
        log.debug('CAG TEST: NO DATA RECORDS')
        stream_handle = StringIO(TEST_DATA_ndr)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(1)

        if result:
            log.debug('CAG TEST: FAILED TO DETECT NO DATA RECORDS CASE')
            self.fail()
        else:
            log.debug('CAG TEST: NO DATA RECORDS DETECTED')
            pass

    def test_simple_with_input_too_short(self):
        """
        Read test data. Should detect that the input stream ?????
        Data stream should be rejected.
        """
        log.debug('CAG TEST: FILE IS TOO SHORT')
        stream_handle = StringIO(TEST_DATA_wts)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(1)
        if result:
            log.debug('CAG TEST: FAILED TO DETECT FILE IS TOO SHORT CASE')
            self.fail()
        else:
            log.debug('CAG TEST: FILE IS TOO SHORT DETECTED')
            pass

    def test_simple_with_wrong_header(self):
        """
        Read test data. Should detect that the input stream ?????
        Data stream should be rejected.
        """
        log.debug('CAG TEST: FILE HAS THE WRONG HEADER')
        stream_handle = StringIO(TEST_DATA_wwh)
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)
        # next get records
        result = parser.get_records(1)
        if result:
            log.debug('CAG TEST: FAILED TO DETECT WRONG HEADER')
            self.fail()
        else:
            log.debug('CAG TEST: WRONG HEADER DETECTED')
            pass

    def test_with_yml(self):
        with open(os.path.join(RESOURCE_PATH, 'node58p1_0.wc_wfp.dat')) as stream_handle:
            parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)

            particles = parser.get_records(50)
            self.assertEqual(len(particles), 50)
            self.assert_particles(particles, 'node58p1_0.wc_wfp.yml', RESOURCE_PATH)

        self.assertEqual(self.exception_callback_value, [])

    def particle_to_yml(self, particles, filename, mode='w'):
        """
        This is added as a testing helper, not actually as part of the parser tests. Since the same particles
        will be used for the driver test it is helpful to write them to .yml in the same form they need in the
        results.yml fids here.
        """
        # open write append, if you want to start from scratch manually delete this fid
        fid = open(os.path.join(RESOURCE_PATH, filename), mode)

        fid.write('header:\n')
        fid.write("    particle_object: 'MULTIPLE'\n")
        fid.write("    particle_type: 'MULTIPLE'\n")
        fid.write('data:\n')

        for i in range(0, len(particles)):
            particle_dict = particles[i].generate_dict()

            fid.write('  - _index: %d\n' % (i+1))

            fid.write('    particle_object: %s\n' % particles[i].__class__.__name__)
            fid.write('    particle_type: %s\n' % particle_dict.get('stream_name'))
            fid.write('    internal_timestamp: %f\n' % particle_dict.get('internal_timestamp'))

            for val in particle_dict.get('values'):
                if isinstance(val.get('value'), float):
                    fid.write('    %s: %16.16f\n' % (val.get('value_id'), val.get('value')))
                else:
                    fid.write('    %s: %s\n' % (val.get('value_id'), val.get('value')))
        fid.close()

    def create_yml(self):
        """
        This utility creates a yml file
        """

        #ADCP_data_20130702.PD0 has one record in it
        fid = open(os.path.join(RESOURCE_PATH, 'node58p1_0.wc_wfp.dat'), 'rb')

        stream_handle = fid
        parser = CtdpfCklWfpSioParser(self.config, stream_handle,
                                      self.exception_callback)

        particles = parser.get_records(800)

        self.particle_to_yml(particles, 'node58p1_0.wc_wfp_ALL.yml')
        fid.close()

