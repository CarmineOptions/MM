
import dataclasses
from datetime import datetime
from json import JSONEncoder
import traceback
from typing import Any
from decimal import Decimal

class CustomJSONEncoder(JSONEncoder):
    def default(self, o: Any):
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)

        if isinstance(o, datetime):
            return o.strftime('%Y %b %d %H:%M:%S.%f')

        if isinstance(o, Exception):
            return {
                "type": type(o).__name__,
                "message": str(o),
                "args": o.args,
                "traceback": traceback.format_exception(type(o), o, o.__traceback__) 
            }

        if isinstance(o, Decimal):
            return str(o)

        try:
            return f'Unable to serialize: {type(o)}: {str(o)}'
        except: 
            return f'Unable serialize or stringify: {(type(o))}'