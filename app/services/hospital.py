# -*- coding: utf-8 -*-


import json
from typing import Optional, Tuple
from datetime import datetime

import inject
import requests
import template_logging
from work_wechat import WorkWeChat, MsgType, TextCard

from app.dependencies import Config, Cache


logger = template_logging.getLogger(__name__)


"""
Service 中不应该出现Schema
理想情况下所有涉及参数校验均应该在dataclass中的__post_init__方法内完成
"""


def get_notify_cache_key(notify_key: str) -> str:
    """
    @param: notify_key 通知类型
    根据notify_key返回本次通知缓存key
    """
    # 获取配置
    config: Config = inject.instance(Config)
    return f"{config.PROJECT_NAME}-{config.RUNTIME_ENV}-{notify_key}"


def skip_notify(notify_key: str) -> Tuple[bool, int]:
    """
    @param: notify_key 通知类型
    判断是否需要跳过本次通知
    """
    # 获取cache
    cache: Cache = inject.instance(Cache)
    # 获取配置
    config: Config = inject.instance(Config)
    cache_key: str = get_notify_cache_key(notify_key)
    # 获得重复推送次数
    _cache_bytes: Optional[bytes] = cache.get_cache(cache_key)
    _notify_times: int = int(_cache_bytes.decode()) if _cache_bytes else 0
    if _notify_times >= config.RESERVE_DUPLICATE_NOTIFY_TIMES:
        return True, _notify_times
    return False, _notify_times


def save_notify_times(notify_key: str, notify_times: int) -> None:
    """
    @param: notify_key 通知类型
    @param: notify_times 当前重复通知多少次
    保存重复通知次数
    """
    # 获取cache
    cache: Cache = inject.instance(Cache)
    # 获取配置
    config: Config = inject.instance(Config)
    cache_key: str = get_notify_cache_key(notify_key)
    cache.store_cache(cache_key, notify_times, config.RESERVE_DUPLICATE_NOTIFY_TIME_LIMIT)



def reserve_notify() -> None:
    """
    预约提醒
    """
    today = datetime.now().strftime("%Y-%m-%d")
    # 获取配置
    config: Config = inject.instance(Config)
    wechat: WorkWeChat = inject.instance(WorkWeChat)

    app_id = config.RESERVE_APP_ID
    doctor_work_nums = config.RESERVE_DOCTOR_WORK_NUMS.split(",")
    if "" in doctor_work_nums:
        doctor_work_nums.remove("")
    dept_code_list = config.RESERVE_DEPT_CODES.split(",")
    if "" in dept_code_list:
        dept_code_list.remove("")

    url = f"https://api.cmsfg.com/api/appointment/Scheduling?AppId={app_id}"
    for doctor_work_num in doctor_work_nums:
        payload = json.dumps(
            {
                "method": "GetScheduling",
                "params": [
                    {
                        "AppId": app_id,
                        "DoctorWorkNum": doctor_work_num,
                        "RegisterType": config.RESERVE_REGISTER_TYPE,
                        "AppointmentType": config.RESERVE_APPOINTMENT_TYPE,
                    }
                ],
            }
        )
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://api.cmsfg.com",
            "Referer": f"https://api.cmsfg.com/app/hospital/{app_id}/index.html?state={app_id}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code != 200:
            # send notify
            return
        json_rsp = response.json()
        doctor_name = json_rsp["result"]["Doctor"]["DoctorName"]
        doctor_level_name = json_rsp["result"]["Doctor"]["DoctorLevelName"]
        for _i in json_rsp["result"]["AppointmentScheduling"]:
            for _j in _i["Schedulings"]:
                can_appointment = _j["CanAppointment"]
                appointment = _j["Appointment"]
                # 科室过滤
                if _j["DeptCode"] not in dept_code_list:
                    logger.info(f"跳过非本次预约科室.")
                    continue
                # 价格过滤
                if _j["Price"] > config.RESERVE_PRICE_LIMIT:
                    logger.info(f"跳过超预算的时间档期.")
                    continue
                # 是否可预约
                if can_appointment - appointment <= 0:
                    logger.info(f"可预约{can_appointment}人，当前已约{appointment}人, 无法预约.")
                    continue
                day = _j["Date"]
                start_time = _j["StartTime"]
                end_time = _j["EndTime"]
                price = _j["Price"]
                location = _j["Location"]
                dept_code = _j["DeptCode"]
                # 同一次预约只提醒1次
                notify_key = f"{doctor_work_num}#{dept_code}#{day}#{start_time}#{end_time}"
                _skip, _notify_times = skip_notify(notify_key)
                if _skip:
                    logger.info(f"skip notify, _notify_times is {_notify_times}")
                    continue
                _notify_times = _notify_times + 1
                wechat.message_send(
                    agentid=config.AGENT_ID,
                    msgtype=MsgType.TEXTCARD,
                    touser=("@all",),
                    textcard=TextCard(
                        title="预约可用提醒",
                        description=(
                            f'日期: <div class="highlight">{day}</div>'
                            f'开始时间: <div class="highlight">{start_time}</div>'
                            f'结束时间: <div class="highlight">{end_time}</div>'
                            f'地点: <div class="highlight">{location}</div>'
                            f'金额: <div class="highlight">{price}</div>'
                            f'医生: <div class="highlight">{doctor_name}</div>'
                            f'职位: <div class="highlight">{doctor_level_name}</div>'
                            f"预约进度: {appointment}/{can_appointment}"
                        ),
                        url=f"https://api.cmsfg.com/app/hospital/{app_id}/index.html?state={app_id}#/DoctorSchedule?AppId={app_id}&DeptCode={dept_code}&RegisterType={config.RESERVE_REGISTER_TYPE}&AppointmentType={config.RESERVE_APPOINTMENT_TYPE}&Date={today}&DoctorWorkNum={doctor_work_num}",
                    ),
                )
                save_notify_times(notify_key, _notify_times)
if __name__ == '__main__':
    pass