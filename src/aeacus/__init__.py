import os

SRC_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PROJECT_PATH = os.path.dirname(SRC_PATH)
RESOURCE_PATH = os.path.join(PROJECT_PATH, 'resources')
RESULTS_PATH = os.path.join(RESOURCE_PATH, 'results')
RESULTS0_PATH = os.path.join(RESOURCE_PATH, 'results0')
DIAGRAM_PATH = os.path.join(RESOURCE_PATH, 'diagrams')
DEMO_SECRETS_PATH = os.path.join(RESOURCE_PATH, 'demo_secrets')
TMP_SECRETS_PATH = os.path.join(RESOURCE_PATH, 'tmp_secrets')
