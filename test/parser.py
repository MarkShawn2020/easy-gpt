from src.lib.parser import parse_api_key

assert parse_api_key('Bearer skxxx') == 'skxxx'
assert parse_api_key('Bearerskxxx') == None
assert parse_api_key('Bearer skxxxs ') == 'skxxxs '
