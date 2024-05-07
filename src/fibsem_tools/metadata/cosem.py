from typing import Iterable, Literal, Optional, Sequence, Tuple, Union
from typing_extensions import deprecated

from pydantic import BaseModel
from xarray import DataArray
from pydantic_zarr.v2 import GroupSpec, ArraySpec
from fibsem_tools.io.util import normalize_chunks
from fibsem_tools.metadata.transform import STTransform


def normalize_paths(
    arrays: Sequence[DataArray], paths: Union[Sequence[str], Literal["auto"]]
):
    if paths == "auto":
        _paths = [f"s{idx}" for idx in range(len(arrays))]
    else:
        _paths = paths
    return _paths


class ScaleMetaV1(BaseModel):
    path: str
    transform: STTransform


class MultiscaleMetaV1(BaseModel):
    name: Optional[str]
    datasets: list[ScaleMetaV1]


class MultiscaleMetaV2(BaseModel):
    name: Optional[str]
    datasets: list[str]


@deprecated(
    "CosemGroupMetadataV1 is deprecated, use multiscale.cosem.GroupAttrs from the cellmap-schemas library instead"
)
class CosemGroupMetadataV1(BaseModel):
    """
    Multiscale metadata used by COSEM for multiscale datasets saved in N5/Zarr groups.
    """

    multiscales: list[MultiscaleMetaV1]

    @classmethod
    def from_xarrays(
        cls,
        arrays: dict[str, DataArray],
        name: Optional[str] = None,
    ):
        """
        Generate multiscale metadata from a sequence of DataArrays.

        Parameters
        ----------

        arrays : Sequence[xarray.DataArray]
            The collection of arrays from which to generate multiscale metadata. These
            arrays are assumed to share the same `dims` attributes, albeit with varying
            `coords`.
        name : Optional[str]
            The name for the multiresolution collection

        Returns
        -------
        COSEMGroupMetadataV1
        """

        multiscales = [
            MultiscaleMetaV1(
                name=name,
                datasets=[
                    ScaleMetaV1(path=path, transform=STTransform.from_xarray(array=arr))
                    for path, arr in arrays.items()
                ],
            )
        ]
        return cls(name=name, multiscales=multiscales)


@deprecated("CosemGroupMetadataV2 is deprecated. Do not use it.")
class CosemGroupMetadataV2(BaseModel):
    """
    Multiscale metadata used by COSEM for multiscale datasets saved in N5/Zarr groups.
    """

    multiscales: list[MultiscaleMetaV2]

    @classmethod
    def from_xarrays(
        cls,
        arrays: Sequence[DataArray],
        paths: Union[Sequence[str], Literal["auto"]] = "auto",
        name: Optional[str] = None,
    ):
        """
        Generate multiscale metadata from a sequence of DataArrays.

        Parameters
        ----------

        arrays : Sequence[xarray.DataArray]
            The collection of arrays from which to generate multiscale metadata. These
            arrays are assumed to share the same `dims` attributes, albeit with varying
            `coords`.
        paths: Union[Sequence[str], Literal["auto"]] = "auto"
            The names for each of the arrays in the multiscale
            collection. If set to "auto", arrays will be named automatically according
            to the scheme `s0` for the largest array, s1 for second largest, and so on.
        name : Optional[str], default is None.
            The name for the multiresolution collection.

        Returns
        -------
        COSEMGroupMetadataV2

        """

        _paths = normalize_paths(arrays, paths)

        multiscales = [
            MultiscaleMetaV2(
                name=name,
                datasets=_paths,
            )
        ]
        return cls(name=name, multiscales=multiscales, paths=_paths)


@deprecated(
    "CosemArrayAttrs is deprecated, use multiscale.cosem.ArrayAttrs from the cellmap-schemas library instead"
)
class CosemArrayAttrs(BaseModel):
    transform: STTransform


@deprecated(
    "CosemMultiscaleArray is deprecated, use multiscale.cosem.Array from the cellmap-schemas library instead"
)
class CosemMultiscaleArray(ArraySpec):
    attributes: CosemArrayAttrs

    @classmethod
    def from_xarray(cls, array: DataArray, **kwargs):
        attrs = CosemArrayAttrs(transform=STTransform.from_xarray(array))
        return cls.from_array(array, attributes=attrs, **kwargs)


@deprecated(
    "CosemMultiscaleGroupV1 is deprecated, use multiscale.cosem.Group from the cellmap-schemas library instead"
)
class CosemMultiscaleGroupV1(GroupSpec):
    attributes: CosemGroupMetadataV1
    members: dict[str, CosemMultiscaleArray]

    @classmethod
    def from_xarrays(
        cls,
        arrays: dict[str, DataArray],
        chunks: Union[Tuple[Tuple[int, ...], ...], Literal["auto"]] = "auto",
        name: Optional[str] = None,
        **kwargs,
    ):
        """
        Convert a collection of DataArray to a GroupSpec with CosemMultiscaleV1 metadata

        Parameters
        ----------

        arrays: dict[str, DataArray]
            The arrays comprising the multiscale image.
        chunks : Union[Tuple[Tuple[int, ...], ...], Literal["auto"]], default is "auto"
            The chunks for the `ArraySpec` instances. Either an explicit collection of
            chunk sizes, one per array, or the string "auto". If `chunks` is "auto" and
            the `data` attribute of the arrays is chunked, then each ArraySpec
            instance will inherit the chunks of the arrays. If the `data` attribute
            is not chunked, then each `ArraySpec` will have chunks equal to the shape of
            the source array.
        paths: Union[Sequence[str], Literal["auto"]] = "auto"
            The names for each of the arrays in the multiscale
            collection. If set to "auto", arrays will be named automatically according
            to the scheme `s0` for the largest array, s1 for second largest, and so on.
        name: Optional[str], default is None
            The name for the multiscale collection.
        **kwargs:
            Additional keyword arguments that will be passed to the `ArraySpec`
            constructor.
        """

        _chunks = normalize_chunks(arrays, chunks)

        attrs = CosemGroupMetadataV1.from_xarrays(arrays, name)

        array_specs = {
            key: CosemMultiscaleArray.from_xarray(arr, chunks=cnks, **kwargs)
            for arr, cnks, key in zip(arrays.values(), arrays.keys(), _chunks)
        }

        return cls(attributes=attrs, members=array_specs)


@deprecated("CosemGroupV2 is deprecated. Do not use it.")
class CosemMultiscaleGroupV2(GroupSpec):
    attributes: CosemGroupMetadataV2
    members: dict[str, CosemMultiscaleArray]

    @classmethod
    def from_xarrays(
        cls,
        arrays: Iterable[DataArray],
        chunks: Union[Tuple[Tuple[int, ...]], Literal["auto"]] = "auto",
        paths: Union[Sequence[str], Literal["auto"]] = "auto",
        name: Optional[str] = None,
        **kwargs,
    ):
        """
        Convert a collection of DataArray to a GroupSpec with CosemMultiscaleV2 metadata

        Parameters
        ----------

        arrays: Iterable[DataArray]
            The arrays comprising the multiscale image.
        chunks : Union[Tuple[Tuple[int, ...], ...], Literal["auto"]], default is "auto"
            The chunks for the `ArraySpec` instances. Either an explicit collection of
            chunk sizes, one per array, or the string "auto". If `chunks` is "auto" and
            the `data` attribute of the arrays is chunked, then each ArraySpec
            instance will inherit the chunks of the arrays. If the `data` attribute
            is not chunked, then each `ArraySpec` will have chunks equal to the shape of
            the source array.
        paths: Union[Sequence[str], Literal["auto"]] = "auto"
            The names for each of the arrays in the multiscale
            collection.
        name: Optional[str], default is None
            The name for the multiscale collection.
        **kwargs:
            Additional keyword arguments that will be passed to the `ArraySpec`
            constructor.
        """

        _paths = normalize_paths(arrays, paths)
        _chunks = normalize_chunks(arrays, chunks)
        attrs = CosemGroupMetadataV2.from_xarrays(arrays, _paths, name)

        array_specs = {
            key: CosemMultiscaleArray.from_xarray(arr, chunks=cnks, **kwargs)
            for arr, cnks, key in zip(arrays, _chunks, _paths)
        }

        return cls(attributes=attrs, members=array_specs)


def multiscale_group(
    *,
    arrays: dict[str, DataArray],
    chunks: Union[tuple[tuple[int, ...]], Literal["auto"]],
    **kwargs,
) -> CosemMultiscaleGroupV1:
    """
    Create a model of a COSEM-style multiscale group from a collection of
    DataArrays

    Parameters
    ----------

    arrays: dict[str, DataArray]
        The data to model.
    chunks: The chunks for each Zarr array in the group.


    """
    return CosemMultiscaleGroupV1.from_xarrays(arrays)
