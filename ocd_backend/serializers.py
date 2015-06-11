import datetime
import msgpack


def decode_datetime(obj):
    res = obj
    if b'__datetime__' in obj:
        try:
            res = datetime.datetime.strptime(obj['as_str'], '%Y-%m-%dT%H:%M:%S.%f')
        except:
            res = None

        if res is not None:
            return res

        try:
            res = datetime.datetime.strptime(obj['as_str'], '%Y-%m-%dT%H:%M:%S')
        except:
            res = None

        if res is not None:
            return res

        # may contain time zone info, disregard for now ... (?)
        res = datetime.datetime.strptime(obj['as_str'][:-6], '%Y-%m-%dT%H:%M:%S')

    return res


def encode_datetime(obj):
    if isinstance(obj, datetime.datetime):
        return {'__datetime__': True, 'as_str': obj.isoformat()}
    return obj


def encoder(obj):
    """
    Encode obj with msgpack, and use custom encoder for datetime objects

    :param obj: value (dict) to encode
    :return: binary document
    """
    return msgpack.packb(obj, default=encode_datetime)


def decoder(obj):
    """
    Reverse of ``encode``; decode objects that was serialized using ``encoder``

    :param obj: binary msgpack
    :return: dict
    """
    return msgpack.unpackb(obj, object_hook=decode_datetime)
