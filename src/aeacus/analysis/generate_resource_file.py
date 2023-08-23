import json
import os
from aeacus import RESOURCE_PATH, RESULTS_PATH


def main():
    quic_support = json.load(open(os.path.join(RESULTS_PATH, "quic_support2.json")))
    ips = json.load(open(os.path.join(RESOURCE_PATH, "alexa_top_500_ip.json")))
    with open(os.path.join(RESULTS_PATH, "quic_support2_ip.txt"), 'w') as f:
        for domain, v in quic_support.items():
            if v == 2:
                if domain in ips:
                    f.write(ips[domain] + '\n')


if __name__ == '__main__':
    main()
