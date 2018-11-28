import os
import h5py
from requests import getvalue_post

DAQ_path = '/home/telescopecontrol/philippe/DAQ/'
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
    # Add to every h5 file the datasets and sort them case insensitive
    for f in pos_files:
        with h5py.File(os.path.join(DAQ_path, 'antenna_positions', f)) as hdf:
            pos_dsets.append([f, sorted(hdf.keys(), key= lambda s: s.lower())])
    for f in readout_files:
        with h5py.File(os.path.join(DAQ_path, 'roachboard_readout/', f)) as hdf:
            readout_dsets.append([f, sorted(hdf.keys(), key= lambda s: s.lower())])
    for f in existing_files:
        with h5py.File(os.path.join(DAQ_path, 'combined_files', f)) as hdf:
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
        dest_file = getvalue_post(request, 'new-file', str)
        if not dest_file or dest_file == 'None':
            dest_file = getvalue_post(request, 'ex-file', str)
        if not dest_file.endswith('.h5'):
            dest_file += '.h5'
        hdf_source = h5py.File(os.path.join(DAQ_path, directory, data_file))
        hdf_dest = h5py.File(os.path.join(DAQ_path, 'combined_files', dest_file), 'a')
        for dset in data_set:
            hdf_source.copy(dset, hdf_dest)
        hdf_dest.close()
        hdf_source.close()
        return ('success', "copied '%s' to '%s'" % (data_set, dest_file))
    except Exception, e:
        return ('error', e)
