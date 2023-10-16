from regex import regex


def parse_api_key(authorization: str):
    m = regex.match(r'^Bearer (sk.*)$', authorization)
    if not m:
        return None
    return m.group(1)
