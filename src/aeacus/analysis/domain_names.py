import json
import os
from urllib.parse import urlparse


def main():
    domain_names = set()
    path = os.path.expanduser('~/Workspace/Aeacus/results/sites_perf')
    for f in os.listdir(path):
        f = os.path.join(path, f)
        data = json.load(open(f))
        site = data['site']
        performance = data['data']
        for p in performance:
            try:
                domain = urlparse(p['name']).netloc
                domain = domain.strip()
                if domain:
                    domain_names.add(domain)
            except Exception as e:
                print(e)
    print(f'Number of domain names: {len(domain_names)}')
    with open(os.path.expanduser('~/Workspace/Aeacus/resources/domain_names.json'), 'w+') as f:
        json.dump(list(domain_names), f)
        


if __name__ == '__main__':
    main()
