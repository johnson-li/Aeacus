import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def crawl(website='google.com'):
    driver = webdriver.Chrome()
    driver.execute_script("performance.setResourceTimingBufferSize(500);")
    driver.get(f'http://{website}')
    js = 'return document.readyState;'
    status = driver.execute_script(js)
    counter = 0
    while status != 'complete':
        print(f'Page not ready: {status}, wait for 1 sec')
        time.sleep(1)
        status = driver.execute_script(js)
        counter += 1
        if counter > 10:
            break
    time.sleep(5)
    js = 'return JSON.stringify(window.performance.getEntries());'
    performance = driver.execute_script(js)
    performance = json.loads(performance)
    json.dump({
        'site': website,
        'data': performance,
    }, open(os.path.expanduser(f'~/Workspace/Aeacus/results/sites_perf/{website}.json'), 'w+'))
    print(f'[{website}] Number of entries: {len(performance)}')
    # for entry in performance:
    #     print(entry['name'], entry.get('initiatorType', None))
    driver.quit()


def main():
    for site in open(os.path.expanduser('~/Workspace/Aeacus/resources/alexa_top_500.txt')).read().splitlines():
        try:
            crawl(site)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main() 
