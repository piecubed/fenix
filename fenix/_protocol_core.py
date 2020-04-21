#!/usr/bin/env python3
#
# Protocol message helpers
#
# Copyright © 2020 by luk3yx
#

import copy
from typing import Any, Dict, Iterable, Iterator, List, Union

class _AutoSlotsMeta(type):
    """
    Automatically adds __slots__ to classes if possible.
    """

    __slots__ = ()
    def __new__(cls, *args): # type: ignore
        if len(args) == 3 and isinstance(args[2], dict):
            d = args[2]
            if '__slots__' not in d:
                annotations = d.get('__annotations__', ())
                for var in annotations:
                    if var in d:
                        break
                else:
                    d['__slots__'] = tuple(annotations)
        return super().__new__(cls, *args)

def _isinstance(obj: Any, typ: Any) -> bool:
    """
    A custom isinstance() which handles typing.Union, typing.List and
    typing.Dict.
    """

    if typ is Any:
        return True
    if not hasattr(typ, '__origin__'):
        if typ is float:
            return isinstance(obj, (int, float))
        return isinstance(obj, typ)

    if typ.__origin__ is Union:
        return any(_isinstance(obj, i) for i in typ.__args__)
    if typ.__origin__ is list:
        if not isinstance(obj, list):
            return False

        # This is not a typo, the comma unpacks __args__ and ensures it only
        # contains one element.
        t, = typ.__args__

        return all(_isinstance(i, t) for i in obj)
    if typ.__origin__ is dict:
        if not isinstance(obj, dict):
            return False

        kt, vt = typ.__args__
        for k, v in obj.items():
            if not _isinstance(k, kt) or not _isinstance(v, vt):
                return False
        return True

    raise NotImplementedError(typ)


class BaseMessage(metaclass=_AutoSlotsMeta):
    """
    Creates a message class.
    """

    def __init__(self, data: Dict[Any, Any]) -> None:
        assert isinstance(data, dict)
        for attr, attr_type in self.__annotations__.items():
            if attr not in data:
                if not hasattr(self, attr):
                    raise KeyError(attr)
                setattr(self, attr, copy.deepcopy(getattr(self, attr)))
                continue

            value = data[attr]
            if not _isinstance(value, attr_type):
                raise TypeError(f'Expected {attr_type!r}, got {value!r}')
            setattr(self, attr, value)

    def __iter__(self) -> Iterator[Any]:
        cls = self.__class__
        for attr in getattr(cls, '__slots__', cls.__annotations__):
            yield getattr(self, attr)
