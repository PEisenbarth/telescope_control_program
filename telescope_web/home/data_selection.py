import os
import h5py
from requests import getvalue

DAQ_path = '/Users/eisenbarth/Desktop/DAQ/'
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
    for f in os.listdir(DAQ_path + 'combined_files'):
        if f.endswith('.h5'):
            existing_files.append(f)

    for f in pos_files:
        with h5py.File(os.path.join(DAQ_path, 'antenna_positions', f)) as hdf:
            pos_dsets.append([f, hdf.keys()])
    for f in readout_files:
        with h5py.File(os.path.join(DAQ_path, 'roachboard_readout/', f)) as hdf:
            readout_dsets.append([f, hdf.keys()])
    for f in existing_files:
        with h5py.File(os.path.join(DAQ_path, 'combined_files', f)) as hdf:
            existing_dsets.append([f, hdf.keys()])

    context = {
        'nbar':         'select_data',
        'positions':    pos_dsets,
        'readouts':     readout_dsets,
        'existing':     existing_dsets,
                    }
    return context

def submit_selection(request):
    try:
        directory = getvalue(request, 'dir', str)
        data_file = getvalue(request, 'file', str)
        data_set = getvalue(request, 'dset', str)
        dest_file = getvalue(request, 'new-file', str)
        print 'dest1' + dest_file
        if not dest_file or dest_file == 'None':
            dest_file = getvalue(request, 'ex-file', str)
            print 'dest2', dest_file
        if not dest_file.endswith('.h5'):
            dest_file += '.h5'

        hdf_source = h5py.File(os.path.join(DAQ_path, directory, data_file))
        print hdf_source.keys()
        hdf_dest = h5py.File(os.path.join(DAQ_path, 'combined_files', dest_file), 'a')
        hdf_source.copy(data_set, hdf_dest)
        return ('success', "copied '%s' to '%s'" % (data_set, dest_file))
    except Exception, e:
        return ('error', e)
