import os

SRC_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PROJECT_PATH = os.path.dirname(SRC_PATH)
RESOURCE_PATH = os.path.join(PROJECT_PATH, 'resources')
RESULTS_PATH = os.path.join(RESOURCE_PATH, 'results')
RESULTS0_PATH = os.path.join(RESOURCE_PATH, 'results0')
RESULTS1_PATH = os.path.join(RESOURCE_PATH, 'results1')
RESULTS2_PATH = os.path.join(RESOURCE_PATH, 'results2')
RESULTS3_PATH = os.path.join(RESOURCE_PATH, 'results3')
DIAGRAM_PATH = os.path.join(RESOURCE_PATH, 'diagrams')
DEMO_SECRETS_PATH = os.path.join(RESOURCE_PATH, 'demo_secrets')
TMP_SECRETS_PATH = os.path.join(RESOURCE_PATH, 'tmp_secrets')
EXP_RESULTS_PATH = os.path.join(RESOURCE_PATH, 'results_exp')