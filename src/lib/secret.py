from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from starlette import status

from src.lib.parser import parse_api_key

_api_key_header = APIKeyHeader(name="Authorization", description="Bearer sk...")


def get_api_key(api_key_header: str = Security(_api_key_header)) -> str:
    """
    :param api_key_header:
    :return:
    """
    # print("api_key_header: ", api_key_header)
    api_key = parse_api_key(api_key_header)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key
