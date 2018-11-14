#!/usr/bin/env python
'''
This script demonstrates programming an FPGA, configuring a wideband spectrometer and plotting the received data using the Python KATCP library along with the katcp_wrapper distributed in the corr package. Designed for use with TUT3 at the 2009 CASPER workshop.\n
self.opts.
You need to have KATCP and CORR installed. Get them from http://pypi.python.org/pypi/katcp and http://casper.berkeley.edu/svn/trunk/projects/packetized_correlator/corr-0.4.0/

\nAuthor: Jason Manley, November 2009.
'''

#TODO: add support for ADC histogram plotting.
#TODO: add support for determining ADC input level 

import corr
import time
import numpy
import struct
import sys
import math
import matplotlib
from datetime import datetime
import time

matplotlib.use('SVG')   # Change backend, otherwise it will throw an error when restarting the Readout
from matplotlib import pyplot as plt
from optparse import OptionParser
import h5py


class RoachReadout():
    def __init__(self):
        self.katcp_port=7147
        self.boffiles = ['tut3.bof',                        #original design with an accu length 2^10
                         'cw_vers_2_2017_Apr_25_1221.bof',  #test()CW readout design with an accu length of 2^9
                         'tut3_hr_v4_2017_May_05_2026.bof'  #CW readout design with an accu length of 2^9
                         ]
        self.bitstream = self.boffiles[2]
        self.acc_len = 2 * (2 ** 28) / 1024
        self.gain = 0x0fffffff
        self.save = False
        self.p = OptionParser()
        self.p.set_usage('spectrometer.py <ROACH_HOSTNAME_or_IP> [options]')
        self.p.set_description(__doc__)
        self.p.add_option('-s', '--skip', dest='skip', action='store_true',
                     help='Skip reprogramming the FPGA and configuring EQ.')
        self.opts, self.args = self.p.parse_args(sys.argv[1:])

        self.roach = 'grasshopper'  # default value for wetton telescope
        self.fpga = None
        self.old_acc_n = None
        self.running = False # As long as readout is true, the data gets plotted
        self.plot_lims = [13750, 13800]


    def get_data(self):
        #get the data...
        ADC_correction = 1.28
        acc_n = self.fpga.read_uint('acc_cnt')

        a_0=struct.unpack('>8192l',self.fpga.read('even',8192*4,0))
        a_1=struct.unpack('>8192l',self.fpga.read('odd',8192*4,0))
        tmsp = time.time()
        interleave_a=[]
        linfloat = numpy.zeros(shape=(16384), dtype=float)
        dBmfloat = numpy.zeros(shape=(16384), dtype=float)

        for i in range(8192):
            interleave_a.append(a_0[i])
            interleave_a.append(a_1[i])

        # normalize the ineger into rmsVolt
        for j in range(16384):  # normalize the integer into rmsVolt
            linfloat[j] = interleave_a[j] / numpy.float64(
                32768 * self.acc_len * 50 * 512 * ADC_correction)  # divided by integration number and 50 Ohm
            if linfloat[j] == 0:
                linfloat[j] = 0.0000001
            dBmfloat[j] = 10 * math.log10(linfloat[j])

        Power = numpy.sum (linfloat) #/numpy.float64(32768)
        if Power == 0:
            Power = 0.0000001
        print "Power in dBm: %s " % (10 * math.log10(Power))
        if self.save and acc_n != self.old_acc_n:
            d = numpy.insert(dBmfloat[self.plot_lims[0]:self.plot_lims[1]], 0, tmsp)
            self.data.append(d)

        return acc_n, dBmfloat, tmsp

    def plot_spectrum(self):
        self.fig = plt.figure(figsize=((7,5)))
        self.ax = self.fig.add_subplot(1,1,1)
        self.running = True
        self.date = datetime.today().date().strftime('%Y_%m_%d')
        self.t = str(datetime.now().time())[:8]
        self.data = []
        while self.running:
            acc_n, interleave_a, tmsp = self.get_data()
            if acc_n != self.old_acc_n: #Draw plot only when acc_n has changed
                plt.clf()
                plt.plot(interleave_a)
                # plt.semilogy(interleave_a)
                plt.title('Integration number %i.'%acc_n)
                plt.ylabel('Power (dBm)')
                plt.ylim()
                plt.ylim(-84,-83)
                plt.grid(True)
                plt.xlabel('Channel')
                # plt.xlim(0, 16384)
                plt.xlim(self.plot_lims[0],self.plot_lims[1])
                plt.plot((13776, 13776), (-84, -83), 'k', linewidth=2.0)
                plt.savefig('/home/telescopecontrol/PhilippE/telescope_control/telescope_web/home/templates/home/roach_plot.html',
                            format='svg')
                # mpld3.save_html(self.fig,
                #                 '/home/telescopecontrol/PhilippE/telescope_control/telescope_web/home/templates/home/roach_plot.html')
                self.old_acc_n = acc_n
            time.sleep(1)

    def run(self):

        try:
            #loggers = []self.opts
            #lh=corr.log_handlers.DebugLogHandler()
            #logger = logging.getLogger(roach)
            #logger.addHandler(lh)
            #logger.setLevel(10)
            print('Connecting to server %s on port %i... ' % (self.roach, self.katcp_port)),
            self.fpga = corr.katcp_wrapper.FpgaClient(self.roach, self.katcp_port, timeout=10)
            time.sleep(1)

            if self.fpga.is_connected():
                print 'ok\n'
            else:
                print 'ERROR connecting to server %s on port %i.\n' % (self.roach, self.katcp_port)
                self.exit_fail()

            print '------------------------'
            print 'Programming FPGA with %s...' %self.bitstream,
            if not self.opts.skip:
                self.fpga.progdev(self.bitstream)
                print 'done'
            else:
                print 'Skipped.'

            print 'Configuring accumulation period...',
            self.fpga.write_int('acc_len',self.acc_len)
            print 'done'

            print 'Resetting counters...',
            self.fpga.write_int('cnt_rst',1)
            self.fpga.write_int('cnt_rst',0)
            print 'done'

            print 'Setting digital gain of all channels to %i...'%self.gain,
            if not self.opts.skip:
                self.fpga.write_int('gain',self.gain) #write the same gain for all inputs, all channels
                print 'done'
            else:
                print 'Skipped.'

            # start the process
            self.plot_spectrum()
            if self.save:
                print 'Saving...'
                with h5py.File('/home/telescopecontrol/PhilippE/DAQ/readout_%s.h5' % self.date, 'a') as hdf:
                    hdf.create_dataset(self.t, data=self.data)
                self.save = False   # Set to False to show that data is saved


        except KeyboardInterrupt:
            self.exit_clean()
        except Exception, e:
            print 'Exception:', e
            self.exit_fail()

        self.exit_clean()

    def exit_fail(self):
        print 'FAILURE DETECTED.'
        try:
            self.fpga.stop()
        except: pass
        raise  Exception('Failure')

    def exit_clean(self):
        try:
            self.fpga.stop()
        except: pass


def start_roach():
    roach = RoachReadout()
    roach.run()

if __name__ == '__main__':
    start_roach()
