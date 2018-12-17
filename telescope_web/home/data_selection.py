import os
import h5py
from requests import getvalue_post
import matplotlib
matplotlib.use('svg')
from matplotlib import pyplot as plt
import mpld3
from mpld3 import utils, plugins
import numpy as np

DAQ_path = '/home/telescopecontrol/philippe/DAQ/'
dest_path = '/home/telescopecontrol/philippe/telescope_control/telescope_web/home/static/combined_files/'
def data_selection(request):
    pos_files = []
    pos_dsets = []
    readout_files = []
    readout_dsets = []
    existing_files = []
    existing_dsets = []
    for f in reversed(os.listdir(DAQ_path + 'antenna_positions')):
        if f.endswith('.h5'):
            pos_files.append(f)
    for f in reversed(os.listdir(DAQ_path + 'roachboard_readout')):
        if f.endswith('.h5'):
            readout_files.append(f)
    for f in os.listdir(dest_path):
        if f.endswith('.h5'):
            existing_files.append(f)
    # Add to every h5 file the datasets and sort them case insensitive
    for f in pos_files:
        with h5py.File(os.path.join(DAQ_path, 'antenna_positions', f)) as hdf:
            pos_dsets.append([f, sorted(hdf.keys(), key= lambda s: s.lower())])
    for f in readout_files:
        with h5py.File(os.path.join(DAQ_path, 'roachboard_readout/', f)) as hdf:
            readout_dsets.append([f, sorted(hdf.keys(), key= lambda s: s.lower())])
    for f in existing_files:
        with h5py.File(os.path.join(dest_path, f)) as hdf:
            existing_dsets.append([f, sorted(hdf.keys(), key= lambda s: s.lower())])
    pos_dsets.sort(reverse=True)
    readout_dsets.sort(reverse=True)
    existing_dsets.sort()
    context = {
        'nbar':         'select_data',
        'positions':    pos_dsets,
        'readouts':     readout_dsets,
        'existing':     existing_dsets,
                    }
    return context

def submit_selection(request):
    try:
        directory = getvalue_post(request, 'dir', str)
        data_file = getvalue_post(request, 'file', str)
        data_set = request.POST.getlist('dset')
        data_set = map(str, data_set)
        dest_file = getvalue_post(request, 'new-file', str)
        if '<' in dest_file or '>' in dest_file:    # Avoid the ability to pass html tags into filename
            raise ValueError("destination file mustn't contain '<' or '>'")
        if not dest_file or dest_file == 'None':
            dest_file = getvalue_post(request, 'ex-file', str)
        if not dest_file.endswith('.h5'):
            dest_file += '.h5'
        hdf_source = h5py.File(os.path.join(DAQ_path, directory, data_file))
        hdf_dest = h5py.File(os.path.join(dest_path, dest_file), 'a')
        in_dest = []
        not_in_dest = []
        for dset in data_set:
            try:
                hdf_source.copy(dset, hdf_dest)
                not_in_dest.append(dset)
            except:
                in_dest.append(dset)
        hdf_dest.close()
        hdf_source.close()
        message = ''
        if len(not_in_dest):
            message += "copied '" + "', '".join(not_in_dest) +  "' to '%s' <br>" %  dest_file
            tag = 'success'
        if len(in_dest):
            message += "'" + "', '".join(in_dest) +  "' already exist in '%s'" % dest_file
            tag = 'error'
        if len(not_in_dest) and len(in_dest):
            tag = 'info'

        return (tag, message)
    except Exception, e:
        return ('error', e)

class LinkedView(plugins.PluginBase):
    """A simple plugin showing how multiple axes can be linked"""

    JAVASCRIPT = """
    mpld3.register_plugin("linkedview", LinkedViewPlugin);
    LinkedViewPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    LinkedViewPlugin.prototype.constructor = LinkedViewPlugin;
    LinkedViewPlugin.prototype.requiredProps = ["idpts", "idline", "data"];
    LinkedViewPlugin.prototype.defaultProps = {}
    function LinkedViewPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    LinkedViewPlugin.prototype.draw = function(){
      var pts = mpld3.get_element(this.props.idpts);
      var line = mpld3.get_element(this.props.idline);
      var data = this.props.data;

      function mouseover(d, i){
        line.data = data[i];
        line.elements().transition()
            .attr("d", line.datafunc(line.data))
            .style("stroke", this.style.fill);
      }
      pts.elements().on("mouseover", mouseover);
    };
    """

    def __init__(self, points, line, linedata):
        if isinstance(points, matplotlib.lines.Line2D):
            suffix = "pts"
        else:
            suffix = None

        self.dict_ = {"type": "linkedview",
                      "idpts": utils.get_id(points, suffix),
                      "idline": utils.get_id(line),
                      "data": linedata}


def plot_dset(request):
    """
    plot the requested dataset
    :return: success/error message, context data
    """

    directory = getvalue_post(request, 'dir', str)
    data_file = getvalue_post(request, 'file', str)
    data_set = request.POST.get('dset')
    dest_file = '/home/telescopecontrol/philippe/telescope_control/telescope_web/home/templates/home/dset_plot.html'
    if not data_set:
        return ('error', 'Please choose a dataset', {})

    if directory == 'roachboard_readout':
        print 'doing roach plot'
        with h5py.File(os.path.join(DAQ_path, directory, data_file)) as hdf:
            hdata = hdf.get(data_set).value
        if data_set.endswith('spectrum'):
            spectrum = [i[1:] for i in hdata]
            time = np.array([i[0] - hdata[0][0] for i in hdata])

            fig, ax = plt.subplots(2, gridspec_kw={'height_ratios': [5, 1]})
            data = np.array([[range(len(spectrum[1])), s] for s in spectrum])

            points = ax[1].scatter(time, 0 * time, s=80, alpha=0.5)

            # create the line object
            ax[0].set_title('%s/%s' % (data_file, data_set))
            lines = ax[0].plot(data[0][0], 0 * data[0][0], '-w', lw=3, alpha=0.5)
            ax[1].set_xlabel('Time')
            ax[1].set_title('Hover over the time points to see the corresponding spectrum')
            ax[0].set_ylim(-84, -83.4)

            # transpose line data and add plugin
            linedata = data.transpose(0, 2, 1).tolist()
            # link the timepoints to the spectra
            plugins.connect(fig, LinkedView(points, lines[0], linedata))

            mpld3.save_html(fig, dest_file)

        if data_set.endswith('power'):
            fig = plt.figure()
            time = [i[0]-hdata[0][0] for i in hdata]
            power = [i[1] for i in hdata]
            plt.plot(time, power)
            plt.title('%s/%s' % (data_file, data_set))
            mpld3.save_html(fig, dest_file)

    elif directory == 'antenna_positions':
        with h5py.File(os.path.join(DAQ_path, directory, data_file)) as hdf:
            print hdf.get(data_set).keys()
            data = hdf.get(data_set + '/' + hdf.get(data_set).keys()[0]).value

        az = [i[1] for i in data]
        el = [i[2] for i in data]
        fig = plt.figure()
        plt.plot(az, el)
        plt.title('%s/%s' % (data_file, data_set))
        plt.xlabel('Azimuth in degree')
        plt.ylabel('Elevation in degree')
        mpld3.save_html(fig, dest_file)

    return ('success', "Plotted '%s'" % data_set, {'plot': True})
