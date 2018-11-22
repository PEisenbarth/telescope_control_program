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
                                     'roach_powermeter_12_bit.bof',
                                    ]
                         }
        if mode in self.boffiles.keys():
            self.mode = mode
        else:
            raise Exception('Unknown mode!')
        self.bitstream = self.boffiles[mode][0]
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
        self.ADC_correction = 1.28
        self.data = []


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
        while self.running:
            acc_n, interleave_a, tmsp = self.get_spectrum()
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
            time.sleep(0.5)

    def get_power(self):
        # get the data...
        print("Get Data")
        total_power = 0.0
        run = False

        while run == False:
            if self.fpga.read_int('acc_cnt') == 0:
                # print "Readout register one!! Loop %s of %s." %(i,samples)
                d = self.fpga.read('one', 65536 * 4, 0)
                tmsp = time.time()
                dint = numpy.array(struct.unpack('>65536l', d))
                for j in range(65536):
                    self.dfloat[j] = dint[j] / numpy.float64(8192 * 4)
                    self.dfloat[j] = numpy.sqrt(self.dfloat[j])
                    self.dfloat[j] = self.dfloat[j] / numpy.float64(512 * self.ADC_correction)
                    self.power[j] = ((self.dfloat[j]) * (self.dfloat[j])) * numpy.float64(20)  # mW output power

                total_power = sum(self.power) / numpy.float64(len(self.power))
                # write here to file
                run = True
            if total_power == 0:
                total_power = 0.0000001
            self.total_power_dbm = 10 * math.log10(total_power)

            # if fpga.read_int('acc_cnt') == 1:
            # print "Readout register one!! Loop %s of %s." %(i,samples)
            #    d = fpga.read('two', 65536 * 4, 0)
            #    dint = numpy.array(struct.unpack('>65536l', d))
            #    for j in range(65536):
            #        dfloat[j] = dint[j] / numpy.float64(8192 * 4)
            #        dfloat[j] = numpy.sqrt(dfloat[j])
            #        dfloat[j] = dfloat[j] / numpy.float64(512 * ADC_correction)
            #        power[j] = ((dfloat[j]) * (dfloat[j])) * numpy.float64(20)

            #    total_power = sum(power) / numpy.float64(len(power))
            #    run = True
            # if total_power == 0:
            #    total_power = 0.0000001

        if len(self.interleave_a) > 1000:
            self.interleave_a.pop(0)
        #if self.save:

        # interleave_a.append(10*numpy.log10(total_power))
        self.interleave_a.append(self.total_power_dbm)
        self.data.append([tmsp, self.total_power_dbm])

        return self.fpga.read_int('acc_cnt'), self.interleave_a

    def plot_power(self):
        self.dfloat = numpy.zeros(shape=(65536), dtype=float)
        self.power = numpy.zeros(shape=(65536), dtype=float)
        self.interleave_a = list()
        self.fig = plt.figure(figsize=((7,5)))
        self.ax = self.fig.add_subplot(1,1,1)
        self.date = datetime.today().date().strftime('%Y_%m_%d')
        self.starttime = str(datetime.now().time())[:8]
        self.data = []
        while self.running:
            acc_n, interleave_a = self.get_power()
            self.fig.clear()
            plt.plot(interleave_a, 'b')
            # matplotlib.pylab.semilogy(interleave_a)
            plt.title('Integration number %i.' % acc_n)
            plt.ylabel('Power (dBm)')
            plt.grid(True)
            plt.xlabel('Channel')
            plt.xlim()
            plt.savefig(
                '/home/telescopecontrol/PhilippE/telescope_control/telescope_web/home/templates/home/roach_plot.html',
                format='svg')

    def run(self):
        self.date = datetime.today().date().strftime('%Y_%m_%d')
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
            if self.mode != 'power':
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
                with h5py.File('/home/telescopecontrol/PhilippE/DAQ/roachboard_readout/readout_%s.h5' % self.date, 'a') as hdf:
                    dset = hdf.create_dataset('%s_mode_%s' % (self.t, self.mode), data=self.data)
                    # Add attributes to the dataset
                    dset.attrs['mode'] = self.mode
                    if self.mode == 'spectrum':
                        dset.attrs['plot_lims'] = self.plot_lims
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

