import json
import os
from matplotlib.cm import ScalarMappable
import numpy as np
import matplotlib.pyplot as plt

from aeacus import RESOURCE_PATH, RESULTS_PATH

RAN_RTT = 10
AEACUS_PROCESS_DELAY = 1.5

def main():
    domains = open(os.path.join(RESOURCE_PATH, 'alexa_top_500.txt')).read().splitlines()
    # quic_support = json.load(open(os.path.join(RESULTS_PATH, "quic_support.json")))
    # domains = list(quic_support.keys())
    ns_delay_data = json.load(open(os.path.join(RESULTS_PATH, 'dns_ns_delay.json')))
    srv_rtt_data = json.load(open(os.path.join(RESOURCE_PATH, 'alexa_top_500_rtt.json')))
    conn_setup_delay_data = {}
    conn_setup_delay_p_data = {}
    records = []
    overall_reduction = [] 
    deployment_data = [[], [], [], []]
    for domain in domains:
        if ns_delay_data.get(domain, {}).get('delay', 0) <= 0 or srv_rtt_data.get(domain, 0) <= 0:
            continue
        ns_delay = ns_delay_data[domain]['delay'] * 1000
        ldns_delay = RAN_RTT
        server_delay = srv_rtt_data[domain] + RAN_RTT
        ldns_server_delay = srv_rtt_data[domain]
        data = {
            'dns_client_hit': server_delay,
            'dns_ldns_hit': server_delay + ldns_delay,
            'dns_ldns_miss': server_delay + ldns_delay + ns_delay,
            'aeacus_up_to_date': server_delay / 2 + ldns_delay / 2 + ldns_server_delay / 2 + AEACUS_PROCESS_DELAY,
            'aeacus_outdated': server_delay / 2 + ldns_delay / 2 + ns_delay + ldns_server_delay / 2 + AEACUS_PROCESS_DELAY,
            }
        conn_setup_delay_data[domain] = data
        conn_setup_delay_p_data[domain] = {k: v / data['dns_client_hit'] * 100 for k, v in data.items()}
        # print(domain, conn_setup_delay_p_data[domain])
        # records.append(1 - data['aeacus_outdated'] / data['dns_ldns_miss'])
        # records.append(1 - data['aeacus_up_to_date'] / data['dns_ldns_miss'])
        records.append(data['aeacus_up_to_date'] / data['dns_ldns_miss'])
        reduction_cache_hit = 1 - data['aeacus_up_to_date'] / data['dns_client_hit']
        reduction_cache_ldns_hit = 1 - data['aeacus_up_to_date'] / data['dns_ldns_hit']
        reduction_cache_miss = 1 - data['aeacus_up_to_date'] / data['dns_ldns_miss']
        overall = 0.8 * reduction_cache_hit + 0.2 * reduction_cache_miss
        overall_reduction.append(overall)
        deployment_data[0].append(server_delay)
        deployment_data[1].append(ns_delay + ldns_delay)
        deployment_data[2].append(reduction_cache_miss)
        deployment_data[3].append(reduction_cache_ldns_hit)
    print('Overall reduction: ', np.mean(overall_reduction))
    print('records: ', min(records), max(records), np.median(records))
    for k in ['dns_ldns_hit', 'dns_ldns_miss', 'aeacus_up_to_date', 'aeacus_outdated']:
        data = [d[k] for d in conn_setup_delay_p_data.values()]
        print(k, np.mean(data), np.std(data))

    cmap = plt.get_cmap("Spectral")
    fig, axes = plt.subplots(1, 2, figsize=(6, 2), sharex=True, sharey=True)
    norm = plt.Normalize(0, 100)
    scale1 = [d * 100 for d in deployment_data[2]]
    scale2 = [d * 100 for d in deployment_data[3]]
    scatter = axes[0].scatter(deployment_data[0], deployment_data[1], c=cmap(norm(scale1)))
    axes[0].set_title('LDNS Cache Miss')
    scatter = axes[1].scatter(deployment_data[0], deployment_data[1], c=cmap(norm(scale2)))
    axes[1].set_title('UE Cache Miss')
    sm =  ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes[1])
    cbar.ax.set_title("%")
    plt.xlim([0, 400])
    plt.ylim([0, 400])
    fig.text(0.5, 0.00, 'RTT to the application server (ms)', ha='center')
    fig.text(0.00, 0.5, 'RTT to the ns (ms)', va='center', rotation='vertical')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_PATH, 'domain_deployment.pdf'))


if __name__ == '__main__':
    main()


