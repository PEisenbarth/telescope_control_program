import h5py
from matplotlib import pyplot as plt

antennaList = ['RTT', 'RTT2']

with h5py.File('DAQ/positions_2018_10_10.h5', 'r') as hdf:
    datagroup = list(hdf.keys())[0]
    antenna = datagroup+'/'+antennaList[0]
    print(antenna)
    data = hdf.get(antenna).value

    az_data = [int(item[1]) for item in data]
    el_data = [int(item[2]) for item in data]


plt.plot(az_data, el_data)
plt.show()