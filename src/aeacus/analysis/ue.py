import json
import os.path

import matplotlib.pyplot as plt
import numpy as np

from aeacus import RESULTS_PATH, DIAGRAM_PATH


def main():
    path = os.path.join(RESULTS_PATH, 'ue.log')
    gps_data = {}
    cellular_data = {}
    for l in open(path).readlines():
        l = l.strip()
        if l:
            l = json.loads(l)
            ts, data = l['ts'], l['data']
            if type(data) == list:
                data = data[0]
                cell_info = data['cellInfo']
                cellular_data[ts] = \
                    (cell_info['cellInfoType'], cell_info['identity']['pci'], cell_info['signalStrength']['rsrq'])
            else:
                gps_data[ts] = (data['latitude'], data['longitude'])
    ts_list = np.array(list(sorted(cellular_data.keys())))
    rsrq_list = [cellular_data[k][2] for k in ts_list]
    ts_list = ts_list[100:]
    rsrq_list = rsrq_list[100:]
    plt.plot(ts_list - ts_list[0], rsrq_list, 'x')
    plt.xlabel('Time (ms)')
    plt.ylabel('RSRQ (dB)')
    plt.savefig(os.path.join(DIAGRAM_PATH, 'ue_rsrq.pdf'))
    plt.close()


if __name__ == '__main__':
    main()
