from enum import Enum


class SysCMD(Enum):
    RUN_PRINT_CONFIG = 'run-print-config'
    RUN_API_SERVER = 'run-api-server'
    RUN_TEST_SERVER = 'run-test-server'
    RUN_BEAT = 'run-beat'
    RUN_BEAT_WORKER = 'run-beat-worker'
    RUN_CUSTOM_WORKER = 'run-custom-worker'
    TEST = 'test'
    MIGRATE = 'migrate'
