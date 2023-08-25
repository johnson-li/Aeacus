import os
import re

from aeacus import RESOURCE_PATH, RESULTS_PATH


def main():
    path = os.path.join(RESULTS_PATH, "eval_tls_err")
    data = []
    for filename in os.listdir(path):
        last_ts = 0
        for line in open(os.path.join(path, filename)).readlines():
            s = re.search(r"\[(\d+.\d+)ms\]", line)
            if s:
                last_ts = float(s.group(1))
            if "TlsFail" in line:
                data.append(last_ts)    
                break
    print(data)


if __name__ == "__main__":
    main()
