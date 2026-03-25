#!/usr/bin/python
# -*- coding: utf-8 -*-
# @desc           : 智能客服查询参数

from fastapi import Depends
from core.dependencies import Paging, QueryParams


class AgentParams(QueryParams):

    def __init__(
            self,
            params: Paging = Depends(),
            keyword: str = None,
            status: str = None,
            service_type: str = None,
    ):
        super().__init__(params)
        self.v_order = "desc"
        self.v_order_field = "create_datetime"
        self.keyword = keyword
        self.status = status
        self.service_type = service_type
