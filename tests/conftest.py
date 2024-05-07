from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal
import numpy as np
import pytest

from xarray import DataArray


@pytest.fixture(scope="function")
def tmp_zarr(tmpdir) -> str:
    path = tmpdir.mkdir("test.zarr")
    return str(path)


@pytest.fixture(scope="function")
def tmp_n5(tmpdir):
    path = tmpdir.mkdir("test.n5")
    return str(path)


def create_coord(
    shape: int,
    dim: str,
    units: str | None,
    scale: float,
    translate: float,
):
    return DataArray(
        (np.arange(shape) * scale) + translate,
        dims=(dim,),
        attrs={"units": units},
    )


def create_array(
    *,
    shape: tuple[int, ...],
    dims: tuple[str, ...],
    units: tuple[str | None, ...],
    scale: tuple[float, ...],
    translate: tuple[float, ...],
    **kwargs: Any,
):
    """
    Create a `DataArray` with a shape and coordinates
    defined by the parameters axes, units, types, scale, translate.
    """
    coords = []
    for dim, unit, shp, scle, trns in zip(dims, units, shape, scale, translate):
        coords.append(
            create_coord(shape=shp, dim=dim, units=unit, scale=scle, translate=trns)
        )

    return DataArray(np.zeros(shape), coords=coords, **kwargs)


@dataclass
class PyramidRequest:
    shape: tuple[int, ...]
    dims: tuple[str, ...] | Literal["auto"] = "auto"
    units: tuple[str, ...] | Literal["auto"] = "auto"
    scale: tuple[float, ...] | Literal["auto"] = "auto"
    translate: tuple[float, ...] | Literal["auto"] = "auto"


@pytest.fixture(scope="function")
def pyramid(request) -> tuple[DataArray, DataArray, DataArray]:
    """
    Create a collection of DataArrays that represent a multiscale pyramid
    """
    param: PyramidRequest = request.param
    shape = param.shape
    if param.dims == "auto":
        dims = tuple(map(str, range(len(shape))))
    else:
        dims = param.dims

    if param.units == "auto":
        units = ("meter",) * len(shape)
    else:
        units = param.units

    if param.scale == "auto":
        scale = (1,) * len(shape)
    else:
        scale = param.scale

    if param.translate == "auto":
        translate = (0,) * len(shape)
    else:
        translate = param.translate

    data = create_array(
        shape=shape, dims=dims, units=units, scale=scale, translate=translate
    )

    coarsen_kwargs = {**{dim: 2 for dim in data.dims}, "boundary": "trim"}
    multi = (data, data.coarsen(**coarsen_kwargs).mean())
    multi += (multi[-1].coarsen(**coarsen_kwargs).mean(),)
    return multi
