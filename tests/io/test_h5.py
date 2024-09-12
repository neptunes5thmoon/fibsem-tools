import os

import h5py
import numpy as np

from fibsem_tools.io.core import access


def test_access_array(tmpdir):
    path = os.path.join(str(tmpdir), "foo.h5")
    key = "s0"
    data = np.random.randint(0, 255, size=(10, 10, 10), dtype="uint8")
    attrs = {"resolution": "1000"}

    with h5py.File(path, mode="w") as h5f:
        arr1 = h5f.create_dataset(key, data=data)
        arr1.attrs.update(**attrs)

    arr2 = access(os.path.join(path, key), mode="r")
    assert dict(arr2.attrs) == attrs
    assert np.array_equal(arr2[:], data)
    arr2.file.close()

    arr3 = access(os.path.join(path, key), data=data, attrs=attrs, mode="w")
    assert dict(arr3.attrs) == attrs
    assert np.array_equal(arr3[:], data)
    arr3.file.close()


def test_access_group(tmpdir):
    key = "s0"
    tmpfile = "test.h5"
    store = os.path.join(str(tmpdir), tmpfile)

    attrs = {"resolution": "1000"}

    grp = access(os.path.join(store, key), attrs=attrs, mode="w")
    assert dict(grp.attrs) == attrs
    grp.file.close()

    grp2 = access(os.path.join(store, key), mode="r")
    assert dict(grp2.attrs) == attrs
    grp2.file.close()

    root_grp = access(store, mode="r")
    assert key in root_grp
    root_grp.file.close()
