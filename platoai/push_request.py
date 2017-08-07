import os
from io import BytesIO
import datetime
import json
import requests


def _serialize(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type {} not serializable".format(type(obj)))


class PushRequest(object):
    """A file-like object used to enqueue a call audio file to be processed by
    Plato AI.

    Args:
        metadata (:obj:`dictionary`): The metadata for the call.
        audio (:obj:`file-like object`): The raw audio bytes of the call.
        url (str, optional): The URL for the API.
    """

    def __init__(self, metadata, audio=None,
                 url='https://api.platoai.com:9000'):

        self.metadata = metadata

        self.url = url

        if not audio:
            audio = BytesIO()
        self.buffer = audio

    def __enter__(self):
        return self

    def read(self, *args, **kwargs):
        return self.buffer.read(*args, **kwargs)

    def write(self, chunk):
        return self.buffer.write(chunk)

    def push(self):
        """Enqueue a call to be processed by Plato AI.

        Returns:
            metadata (:obj:`dictionary`): The metadata for the uploaded call.
        """
        self.buffer.seek(0)

        payload = json.dumps(self.metadata, default=_serialize)
        files = {
            'metadata': (None, payload, 'application/json'),
            'file': (self.metadata.get('identifier'), self.buffer,
                     'application/octet-stream')
        }

        r = requests.post('{}/enqueue'.format(self.url), files=files)
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            raise RuntimeError(r.content)

    def close(self):
        self.buffer.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
