# -*- coding: utf-8 -*-


from typing import Optional, List, Any

import template_logging
from template_pagination import IPagePaginationParam, IPaginationRes, ISortParam, ISortType

logger = template_logging.getLogger(__name__)


def do_after_paginate_handler(pagination_res: IPaginationRes, **_user_kwargs: Any) -> IPaginationRes:
    """
    分页后操作, 可以进行一些分页后处理
    一些兼容的事情在这里做
    """
    return pagination_res


def get_page_paginate_params_handler(**_user_kwargs: Any) -> IPagePaginationParam:
    """
    这是一个简单的实现
    传递分页参数
    可以不实现该handler,
    直接在flask before_request中手动调用set_page_pagination_params/set_offset_pagination_params
    也是一条支持的路径,手动调用set的优先级更高
    """
    from flask import request
    page: int = int(request.args.get('page', 1))
    limit: int = int(request.args.get('per_page', 20))
    order_by: Optional[List[ISortParam]] = None

    # 这里假设以id:desc,created_at:desc的形式
    sort_str: str = request.args.get('sort_str')
    sort_arr: Optional[List[str]] = sort_str.split(',') if sort_str else None

    # 构造参数
    pagination_param: IPagePaginationParam = IPagePaginationParam(limit, order_by, page)
    if not sort_arr:
        return pagination_param
    order_by = list()
    # 获取排序
    for express in sort_arr:
        _label, _func_str = express.split(':')
        _func_type: ISortType = ISortType.DESC if str(_func_str).lower() == 'desc' else ISortType.ASC
        _sort_param: ISortParam = ISortParam(_label, _func_type)
        order_by.append(_sort_param)
    pagination_param.order_by = order_by
    return pagination_param
