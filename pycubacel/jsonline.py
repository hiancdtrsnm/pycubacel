import io
import gzip
import json as _json
from array import array
from typing import Union
from pathlib import Path
from functools import partial
from collections import OrderedDict
import collections.abc as collections_abc

SEPARATORS = (', ', ': ')
class json:
    __slots__ = ()
    dump = partial(_json.dump, separators=SEPARATORS, ensure_ascii=True)
    dumps = partial(_json.dumps, separators=SEPARATORS, ensure_ascii=True)
    load = _json.load
    loads = _json.loads

class LRUCache:
    __slots__ = ("_cache", "_capacity")

    def __init__(self, capacity: int):
        self._cache = OrderedDict()
        self._capacity = capacity

    def __contains__(self, key):
        return key in self._cache

    def get(self, key, default=None, raise_KeyError=False):
        cache = self._cache
        if key in cache:
            cache.move_to_end(key)
            return cache[key]
        if raise_KeyError:
            raise KeyError(key)
        return default

    def put(self, key, value):
        cache = self._cache
        cache[key] = value
        cache.move_to_end(key)
        if len(cache) > self._capacity:
            cache.popitem(last=False)

    def pop(self, key, default=None):
        self._cache.pop(key, default)

    def clear(self):
        self._cache.clear()

class PositionArray(collections_abc.MutableSequence):
    __Slots__ = ('_data')
    def __init__(self):
        self._data = array('Q')

    def dump(self, f):
        self._data.tofile(f)

    @staticmethod
    def load(f):
        ar = array('Q')
        data = f.read(1024)
        while data != b'':
            ar.frombytes(data)
            data = f.read(1024)
        par = PositionArray()
        par._data = ar
        return par

    @property
    def data(self):
        return self._data

    def __len__(self):
        return len(self._data)//2

    def _validate_index(self, idx):
        index_bound = len(self._data)//2
        if -index_bound > idx or idx >= index_bound:
            raise IndexError

    def __getitem__(self, idx):
        self._validate_index(idx)
        data = self._data
        return (data[idx*2], data[2*idx+1])

    def __setitem__(self, idx, item):
        self._validate_index(idx)
        data = self._data
        data[idx*2], data[idx*2+1] = item

    def __delitem__(self, idx):
        self._validate_index(idx)
        self._data.pop(2*idx)
        self._data.pop(2*idx)

    def insert(self, idx, item):
        index_bound = len(self._data)//2
        if idx > index_bound or idx < 0:
            raise IndexError
        self._data.insert(idx*2, item[1])
        self._data.insert(idx*2, item[0])


class jsonLine(collections_abc.Sequence):
    __slots__ = ('_index', '_index_path', '_data_path',
                 '_data_file', '_cache')
    def __init__(self, path: Union[str, Path], default=None, cache_size=10):
        if default is not None:
            json.dump = partial(json.dump, default=default)
            json.dumps = partial(json.dumps, default=default)
        pth = Path(path)
        name = pth.name
        pth = pth.parent
        self._index = PositionArray()
        self._index_path = pth/(name+'.json.idx')
        self._data_path = pth/(name+'.json')
        if not self._data_path.exists():
            self._data_path.touch()
            with self._index_path.open('w'):
                pass
            self._data_file = self._data_path.open('r', encoding='ascii')
        else:
            self._data_file = self._data_path.open('r', encoding='ascii')
            if not self._index_path.exists():
                self._build_index()
            else:
                self._load_index()
        self._cache = LRUCache(cache_size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _dump_index(self):
        with gzip.open(self._index_path, 'wb', compresslevel=9) as f:
            self._index.dump(f)

    def _load_index(self):
        with gzip.open(self._index_path, 'rb') as f:
            self._index = PositionArray.load(f)

    def _read_chunk(self, position, n_bytes):
        file = self._data_file
        file.seek(position)
        data = file.read(n_bytes)
        return data

    def __len__(self):
        return len(self._index)

    def __getitem__(self, idx):
        index = self._index
        if -len(index) > idx or idx >= len(index):
            raise IndexError
        if idx in self._cache:
            return self._cache.get(idx)
        idx1 = index[idx]
        data = json.loads(self._read_chunk(idx1[0], idx1[1]))
        self._cache.put(idx, data)
        return data

    def get(self, idx, default=None):
        try:
            return self[idx]
        except IndexError:
            return default

    def append(self, data):
        jdata = json.dumps(data)
        self._data_file.close()
        with self._data_path.open('a', encoding='ascii') as f:
            f.seek(0, 2) # jump to the end of the file
            idx = f.tell() # get the actual position in the file
            offset = 0
            offset += f.write(jdata)
            offset += f.write('\n')
            self._index.append((idx, offset))
        self._data_file = self._data_path.open('r', encoding='ascii')
        self._dump_index()

    def extend(self, data):
        self._data_file.seek(0, 2) # jump to the end of the file
        end_idx = self._data_file.tell() # get the actual position in the file
        self._data_file.close()
        buffer = io.BytesIO()
        f = io.TextIOWrapper(buffer, encoding='ascii', write_through=True)
        for dat in data:
            jdata = json.dumps(dat)
            idx = f.tell()+end_idx # get the actual position in the file
            offset = 0
            offset += f.write(jdata)
            offset += f.write('\n')
            self._index.append((idx, offset))
        with self._data_path.open('ab') as f:
            f.write(buffer.getvalue())
        self._data_file = self._data_path.open('r', encoding='ascii')
        self._dump_index()

    def close(self):
        if not self._data_file.closed:
            self._data_file.close()

    def _build_index(self):
        file = self._data_file
        file.seek(0) # jump to the being of the file
        index = PositionArray()
        idx = file.tell()
        data = file.readline()
        while data != '':
            pos = file.tell()
            index.append((idx, pos-idx-1))
            idx = pos
            data = file.readline()
        self._index = index
        self._dump_index()

    def rebuild_index(self):
        self._build_index()

def open(path: Union[str, Path], default=None, cache=10):
    return jsonLine(path, default, cache)
