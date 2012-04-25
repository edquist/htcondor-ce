import osgtest.library.core as core
import osgtest.library.files as files

import re
import os
import pwd
import shutil
import socket
import unittest
import ConfigParser

"""
Testing number conventions:
 001-009 - Configuration, making proxy, etc
 010-019 - Tests that don't require the rsv service to be running
 020-029 - Tests for the tools that require the rsv service to be running
 030-049 - Testing of metrics that don't require any other services
 050-079 - Testing of metrics that require a CE
 080-099 - Testing of metrics that require an SE
 100-120 - Testing of consumers
"""

core.config['rsv.config-file'] = '/etc/osg/config.d/30-rsv.ini'

class TestRSV(unittest.TestCase):

    host = socket.getfqdn()

    def start_rsv(self):
        core.check_system(('rsv-control', '--on'), 'rsv-control --on')
        return
    
    def stop_rsv(self):
        core.check_system(('rsv-control', '--off'), 'rsv-control --off')
        return
    
    def config_and_restart(self):
        self.stop_rsv()
        core.check_system(('osg-configure', '-c', '-m', 'rsv'), 'osg-configure -c -m rsv')
        self.start_rsv()
        return


    def run_metric(self, metric, host=host):
        command = ('rsv-control', '--run', '--host', host, metric)
        stdout = core.check_system(command, ' '.join(command))[0]

        self.assert_(re.search('metricStatus: OK', stdout) is not None)
        return


    def test_001_set_config_vals(self):
        core.config['rsv.certfile'] = "/etc/grid-security/rsv/rsvcert.pem"
        core.config['rsv.keyfile'] = "/etc/grid-security/rsv/rsvkey.pem"
        
    def test_002_setup_certificate(self):
        if core.missing_rpm('rsv'):
            return

        # TODO - on fermicloud machines we copy the hostcert.  Can we do better?
        if not os.path.exists(os.path.dirname(core.config['rsv.certfile'])):
            os.makedirs(os.path.dirname(core.config['rsv.certfile']))
        if not os.path.exists(core.config['rsv.certfile']):
            shutil.copy('/etc/grid-security/hostcert.pem', core.config['rsv.certfile'])
        if not os.path.exists(core.config['rsv.keyfile']):
            shutil.copy('/etc/grid-security/hostkey.pem', core.config['rsv.keyfile'])

        (rsv_uid, rsv_gid) = pwd.getpwnam('rsv')[2:4]
        os.chown(core.config['rsv.certfile'], rsv_uid, rsv_gid)
        os.chmod(core.config['rsv.certfile'], 0444)
        os.chown(core.config['rsv.keyfile'], rsv_uid, rsv_gid)
        os.chmod(core.config['rsv.keyfile'], 0400)
        return


    def test_003_setup_grid_mapfile(self):
        if core.missing_rpm('rsv'):
            return

        # Register the cert in the gridmap file
        cert_subject = core.certificate_info(core.config['rsv.certfile'])[0]

        # TODO - should we restore the grid-mapfile after RSV tests finish?
        files.append_line('/etc/grid-security/grid-mapfile', '"%s" rsv' % (cert_subject))
        return
    

    def test_004_load_default_config(self):
        if core.missing_rpm('rsv'):
            return

        # We'll pull in the default config file and store it.  We might want to
        # do tests based on the default.
        self.config = ConfigParser.RawConfigParser()
        self.config.optionxform = str
        self.config.read(core.config['rsv.config-file'])
        core.config['rsv.default-config'] = self.config
        return


    def test_010_version(self):
        if core.missing_rpm('rsv'):
            return

        command = ('rsv-control', '--version')
        stdout = core.check_system(command, 'rsv-control --version')[0]

        # The rsv-control --version just returns a string like '1.0.0'.
        self.assert_(re.search('\d.\d.\d', stdout) is not None)
        return


    def test_011_list(self):
        if core.missing_rpm('rsv'):
            return

        command = ('rsv-control', '--list', '--all')
        stdout = core.check_system(command, 'rsv-control --list --all')[0]

        # I don't want to parse the output too much, but we know that most
        # of the metrics start with 'org.osg.'.  So just check for that string
        # once and we'll call it good enough.
        self.assert_(re.search('org.osg.', stdout) is not None)
        return


    def test_012_list_with_cron(self):
        if core.missing_rpm('rsv'):
            return
        
        command = ('rsv-control', '--list', '--all', '--cron')
        stdout = core.check_system(command, 'rsv-control --list --all')[0]

        # One of the header columns will say 'Cron times'
        self.assert_(re.search('Cron times', stdout) is not None)
        return


    def test_013_profiler(self):
        if core.missing_rpm('rsv'):
            return

        profiler_tarball = 'rsv-profiler.tar.gz'
        
        command = ('rsv-control', '--profile')
        stdout = core.check_system(command, 'rsv-control --profile')[0]
        self.assert_(re.search('Running the rsv-profiler', stdout) is not None)
        self.assert_(os.path.exists(profiler_tarball))
        files.remove(profiler_tarball)
        return


    def test_024_rsv_control_bad_arg(self):
        if core.missing_rpm('rsv'):
            return
        
        command = ('rsv-control', '--kablooey')
        (ret, out, err) = core.system(command, 'rsv-control --kablooey')
        self.assert_(ret != 0)
        return


    def test_020_stop_rsv(self):
        if core.missing_rpm('rsv'):
            return

        self.stop_rsv()
        return


    def test_021_start_rsv(self):
        if core.missing_rpm('rsv'):
            return
        
        self.start_rsv()
        return


    def test_022_job_list(self):
        if core.missing_rpm('rsv'):
            return

        command = ('rsv-control', '--job-list')
        stdout = core.check_system(command, 'rsv-control --job-list')[0]

        # TODO
        # Make sure that the header prints at least.  We can improve this
        self.assert_(re.search('OWNER', stdout) is not None)
        return


    def test_023_job_list_parsable(self):
        if core.missing_rpm('rsv'):
            return

        # This test is currently failing because there are no enabled metrics.  Until
        # we add some RSV configuration to enable metrics.
        
        # Check the parsable job-list output
        #command = ('rsv-control', '--job-list', '--parsable')
        #stdout = core.check_system(command, 'rsv-control --job-list --parsable')[0]

        # The separator is a pipe, so just make sure we got one of those
        #self.assert_(re.search('\|', stdout) is not None)
        return


    def test_030_ping_metric(self):
        if core.missing_rpm('rsv'):
            return

        self.run_metric('org.osg.general.ping-host')
        return


    def test_031_hostcert_expiry_metric(self):
        if core.missing_rpm('rsv'):
            return

        self.run_metric('org.osg.local.hostcert-expiry')
        return


    def test_050_gram_authentication_metric(self):
        if core.missing_rpm('rsv', 'globus-gatekeeper'):
            return

        self.run_metric('org.osg.globus.gram-authentication')
        return

    def test_051_osg_version_metric(self):
        if core.missing_rpm('rsv', 'globus-gatekeeper'):
            return

        self.run_metric('org.osg.general.osg-version')
        return

    def test_052_vo_supported_metric(self):
        if core.missing_rpm('rsv', 'globus-gatekeeper'):
            return

        self.run_metric('org.osg.general.vo-supported')
        return



    def test_100_html_consumer(self):
        # This test must come after some of the metric tests so that we have
        # some job records to use to create an index.html
        if core.missing_rpm('rsv'):
            return

        index_file = "/usr/share/rsv/www/index.html"

        # We are going to make sure the html-consumer runs, and that the index
        # file is updated.
        old_mtime = os.stat(index_file).st_mtime

        stdout = core.check_system("su -c '/usr/libexec/rsv/consumers/html-consumer' rsv", "run html-consumer", shell=True)[0]
        self.assert_('html-consumer initializing' in stdout)


        new_mtime = os.stat(index_file).st_mtime
        self.assert_(old_mtime != new_mtime)
        return


    #def test_101_fetch_index_via_apache(self):
    #    if core.missing_rpm('rsv', 'httpd'):
    #        return
    #
    #    return

# Test to write:
# - run gratia-consumer?
# - run other metrics?
#     org.osg.batch.jobmanagers-available                       | OSG-CE
#     org.osg.certificates.cacert-expiry                        | OSG-CE
#     org.osg.certificates.crl-expiry                           | OSG-CE
#     org.osg.general.osg-directories-CE-permissions            | OSG-CE
