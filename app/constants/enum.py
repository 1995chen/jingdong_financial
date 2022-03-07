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


class GoldPriceState(Enum):
    # 金价涨到目标价格
    RISE_TO_TARGET_PRICE = 'rise_to_target_price'
    # 金价跌到目标价格
    FALL_TO_TARGET_PRICE = 'fall_to_target_price'
    # 金价上涨了目标价格
    REACH_TARGET_RISE_PRICE = 'reach_target_rise_price'
    # 金价下跌了目标价格
    REACH_TARGET_FALL_PRICE = 'reach_target_fall_price'
