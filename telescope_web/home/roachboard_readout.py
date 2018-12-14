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
matplotlib.use('SVG')   # Change backend, otherwise it will throw an error when restarting the Readout

from datetime import datetime
from matplotlib import pyplot as plt
import time
from optparse import OptionParser
import h5py


class RoachReadout():
    '''
    This class contains all readout possibilities (until now: spectrum, power)
    '''
    def __init__(self, mode):
        '''
        :param mode: str, readout mode  
        '''
        self.katcp_port=7147
        self.boffiles = {'spectrum':['tut3_hr_v4_2017_May_05_2026.bof', #CW readout design with an accu length of 2^9
                                     'cw_vers_2_2017_Apr_25_1221.bof',  #test()CW readout design with an acc_len of 2^9
                                     'tut3.bof',                        # original design with an accu length 2^10
                                    ],
                         'power':   [
                                     'tut3_hr_v4_2017_May_05_2026.bof',
                                     'roach_powermeter_12_bit.bof',
                                    ]
                         }
        if mode in self.boffiles.keys():
            self.mode = mode
        else:
            raise Exception('Unknown mode!')
        self.bitstream = self.boffiles[mode][0]
        self.acc_len = 2**19
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
        self.old_acc_n = 0
        self.running = False # As long as readout is true, the data gets plotted
        self.plot_xlims = None
        self.plot_ylims = None
        self.ADC_correction = 1.28
        self.data = []
        self.directory = '/home/telescopecontrol/philippe/DAQ/roachboard_readout/'
        date = datetime.today().date().strftime('%Y_%m_%d')
        self.filename = 'readout_%s.h5' % date


    def get_spectrum(self):
        # get the data...
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
                32768 * self.acc_len * 50 * 512 * self.ADC_correction)  # divided by integration number and 50 Ohm
            if linfloat[j] == 0:
                linfloat[j] = 0.0000001
            dBmfloat[j] = 10 * math.log10(linfloat[j])

        if self.save and acc_n != self.old_acc_n and acc_n > 2:
            # add tmsp at index 0 to the spectrum
            d = numpy.insert(dBmfloat[self.save_limits[0]:self.save_limits[1]], 0, tmsp)
            self.data.append(d)

        return acc_n, dBmfloat, tmsp

    def plot_spectrum(self):
        if not self.plot_ylims:
            self.plot_ylims = [-84, -83]
        if not self.plot_xlims:
            self.plot_xlims = [13750, 13800]
        self.fig = plt.figure(figsize=((7,5)))
        self.ax = self.fig.add_subplot(1,1,1)
        self.save_limits = self.plot_xlims
        while self.running:
            acc_n, interleave_a, tmsp = self.get_spectrum()
            if acc_n != self.old_acc_n: #Draw plot only when acc_n has changed
                plt.clf()
                plt.plot(interleave_a)
                # plt.semilogy(interleave_a)
                plt.title('Integration number %i.'%acc_n)
                plt.ylabel('Power (dBm)')
                plt.ylim(self.plot_ylims[0],self.plot_ylims[1])
                plt.xlim(self.plot_xlims[0], self.plot_xlims[1])
                plt.grid(True)
                plt.xlabel('Channel')
                # plt.xlim(0, 16384)
                plt.plot((13776, 13776), (self.plot_ylims[0], self.plot_ylims[1]), 'k', linewidth=2.0)
                plt.savefig('/home/telescopecontrol/philippe/telescope_control/telescope_web/home/templates/home/roach_plot.html',
                            format='svg')
                # mpld3.save_html(self.fig,
                #                 '/home/telescopecontrol/philippe/telescope_control/telescope_web/home/templates/home/roach_plot.html')
                self.old_acc_n = acc_n
                self.fig.clear()
            time.sleep(0.5)

    def get_power(self):
        # get the data...
        acc_n = self.fpga.read_uint('acc_cnt')
        dBm_sum = None
        tmsp = None
        while acc_n == self.old_acc_n or acc_n < 2:
            acc_n = self.fpga.read_uint('acc_cnt')
            if acc_n != self.old_acc_n and acc_n > 1:
                a_0=struct.unpack('>8192l',self.fpga.read('even',8192*4,0))
                a_1=struct.unpack('>8192l',self.fpga.read('odd',8192*4,0))
                tmsp = time.time()
                interleave_a=[]
                linfloat = numpy.zeros(shape=(16384), dtype=float)

                for i in range(8192):
                    interleave_a.append(a_0[i])
                    interleave_a.append(a_1[i])

                # normalize the ineger into rmsVolt
                for j in range(16384):  # normalize the integer into rmsVolt
                    linfloat[j] = interleave_a[j] / numpy.float64(
                        32768 * self.acc_len * 50 * 512 * self.ADC_correction)  # divided by integration number and 50 Ohm
                    if linfloat[j] == 0:
                        linfloat[j] = 0.0000001


                lin_sum = numpy.sum(linfloat[self.plot_xlims[0]:self.plot_xlims[1]])
                if lin_sum == 0:
                    lin_sum = 0.0000001
                dBm_sum = (10 * math.log10(lin_sum))
                if self.save and acc_n > 2:
                    self.data.append([tmsp, dBm_sum])
            else:
                time.sleep(0.5)

        return acc_n, dBm_sum, tmsp

    def plot_power(self):
        self.fig = plt.figure(figsize=((7,5)))
        self.ax = self.fig.add_subplot(1,1,1)
        if not self.plot_ylims:
            self.plot_ylims = [-61.2, -60.9]
            plt.ylim(self.plot_ylims)
        if not self.plot_xlims:
            self.plot_xlims = [13660, 13850]
        total_power = []
        while self.running:
            acc_n, power, tmsp = self.get_power()
            if acc_n != self.old_acc_n: #Draw plot only when acc_n has changed
                total_power.append(power)
                if len(total_power) > 300:
                    total_power.pop(0)
                plt.plot(total_power, '-b')
                if self.plot_ylims:
                    plt.ylim(self.plot_ylims)
                plt.title('Data points %s ' % (acc_n-1))
                plt.xlabel('Channel')
                plt.ylabel('Power (dBm)')
                plt.grid(True)
                plt.savefig('/home/telescopecontrol/philippe/telescope_control/telescope_web/home/templates/home/roach_plot.html',
                            format='svg')
                self.fig.clear()
                # mpld3.save_html(self.fig,
                #                 '/home/telescopecontrol/philippe/telescope_control/telescope_web/home/templates/home/roach_plot.html')
                self.old_acc_n = acc_n
            time.sleep(0.5)

    def run(self):
        self.t = str(datetime.now().time())[:8]
        self.running = True
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
            if self.mode == 'spectrum' and not self.acc_len:
                if not self.acc_len:
                    self.acc_len = 2 * (2 ** 28) / 1024
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
            if self.mode == 'spectrum':
                self.plot_spectrum()
            if self.mode == 'power':
                self.plot_power()
            if self.save:
                print 'Saving...'
                with h5py.File(self.directory + self.filename, 'a') as hdf:
                    dset = hdf.create_dataset('%s_%s' % (self.t, self.mode), data=self.data)
                    # Add attributes to the dataset
                    dset.attrs['mode'] = self.mode
                    if self.mode == 'spectrum':
                        dset.attrs['plot_xlims'] = self.plot_xlims
                    dset.attrs['boffile'] = self.bitstream
                    dset.attrs['acc_len'] = self.acc_len
                    dset.attrs['gain'] = self.gain
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

if __name__ == '__main__':
    roach = RoachReadout('spectrum')
    roach.run()
    time.sleep(10)
    roach.running = False

