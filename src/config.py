from enum import Enum


class ApiBase(str, Enum):
    hongda_81 = 'http://49.51.186.136:81/v1'
    xmind = 'http://211.159.172.4:90/v1'


class OutputMode:
    # 原生返回，开销较大，适合debug与前端对接
    raw = 'raw'

    # 核心内容返回，开销较小，性能更高
    plain = 'plain'
