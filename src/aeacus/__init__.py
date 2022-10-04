import os

SRC_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PROJECT_PATH = os.path.dirname(SRC_PATH)
RESOURCE_PATH = os.path.join(PROJECT_PATH, 'resources')
DEMO_SECRETS_PATH = os.path.join(RESOURCE_PATH, 'demo_secrets')
