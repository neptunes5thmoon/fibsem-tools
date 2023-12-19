from typing import Dict, List, Optional, Sequence, Tuple, Union, Literal

from pydantic import BaseModel, root_validator
from xarray import DataArray
import fibsem_tools.io.xr as fsxr


class STTransform(BaseModel):
    """
    Representation of an N-dimensional scaling -> translation transform for labelled
    axes with units.

    Attributes
    ----------

    axes: Sequence[str]
        Names for the axes of the data.
    units: Sequence[str]
        Units for the axes of the data.
    translate: Sequence[float]
        The location of the origin of the data, in units given specified by the `units`
        attribute.
    scale: Sequence[float]
        The difference between adjacent coordinates of the data, in units specified by
        the `units` attribute. Note that when converting an array index into a
        coordinate, the scaling should be applied before translation.
    order:
        Defines the array indexing convention assumed by the other metadata fields.
        Must be "C", which denotes C-ordered indexing, or "F", which denotes F-ordered
        indexing. Tools in the N5 ecosystem express axes in "F" order, contrary to the
        "C" order that is native to python. This attribute allows an N5-based tool to
        express a scaling + translation in the axis order that is native to that
        ecosystem, while retaining compatibility with python-based tools.

        The default is "C".
    """

    order: Optional[Literal["C", "F"]] = "C"
    axes: Sequence[str]
    units: Sequence[str]
    translate: Sequence[float]
    scale: Sequence[float]

    @root_validator
    def validate_argument_length(
        cls, values: Dict[str, Union[Sequence[str], Sequence[float]]]
    ):
        scale = values.get("scale")
        axes = values.get("axes")
        units = values.get("units")
        translate = values.get("translate")
        if not len(axes) == len(units) == len(translate) == len(scale):
            raise ValueError(
                f"""
                The length of all arguments must match. len(axes) = {len(axes)}, 
                len(units) = {len(units)}, len(translate) = {len(translate)}, 
                len(scale) = {len(scale)}"""
            )
        return values

    def to_coords(self, shape: Tuple[int, ...]) -> List[DataArray]:
        """
        Given an array shape, return a list of DataArrays representing a
        bounded coordinate grid derived from this transform. This list can be used as
        the `coords` argument to construct a DataArray.

        Parameters
        ----------

        shape: Tuple[int, ...]
            The shape of the coordinate grid, e.g. the size of the array that will be
            annotated with coordinates.

        Returns
        -------
        List[DataArray]
            A list of DataArrays, one per axis.

        """
        if self.order == "C":
            axes = self.axes
        else:
            axes = reversed(self.axes)
        return [
            fsxr.stt_coord(
                shape[idx],
                dim=k,
                scale=self.scale[idx],
                translate=self.translate[idx],
                unit=self.units[idx],
            )
            for idx, k in enumerate(axes)
        ]

    @classmethod
    def from_coords(
        cls, coords: Sequence[DataArray], order: Literal["C", "F"] = "C"
    ) -> "STTransform":
        """
        Generate a spatial transform from coordinates.

        Parameters
        ----------

        coords: Sequence[xarray.DataArray]
            A sequence of 1D DataArrays, one per dimension.
        order: Literal["C", "F"]
            The array indexing order to use. "C" denotes numpy-style lexicographic indexing
        Returns
        -------

        STTransform
            An instance of STTransform that is consistent with `coords`.
        """

        axes = []
        units = []
        scale = []
        translate = []

        for c in coords:
            if len(c) < 2:
                raise ValueError(
                    f"The coordinate with dims = {c.dims} does not have enough elements to calculate "
                    "a scaling transformation. A minimum of 2 elements are needed."
                )
            axes.append(str(c.dims[0]))
            # default unit is m
            units.append(c.attrs.get("units", "m"))
            translate.append(float(c[0]))
            scale.append(abs(float(c[1]) - float(c[0])))
            assert scale[-1] > 0

        return cls(
            axes=axes, units=units, translate=translate, scale=scale, order=order
        )

    @classmethod
    def from_xarray(cls, array: DataArray, reverse_axes: bool = False) -> "STTransform":
        """
        Generate a spatial transform from a DataArray.

        Parameters
        ----------

        array: xarray.DataArray
            A DataArray with coordinates that can be expressed as scaling + translation
            applied to a regular grid.
        reverse_axes: boolean, default=False
            If `True`, the order of the `axes` in the spatial transform will
            be reversed relative to the order of the dimensions of `array`, and the
            `order` field of the resulting STTransform will be set to "F". This is
            designed for compatibility with N5 tools.

        Returns
        -------

        STTransform
            An instance of STTransform that is consistent with the coordinates defined
            on the input DataArray.
        """

        orderer = slice(None)
        output_order = "C"
        if reverse_axes:
            orderer = slice(-1, None, -1)
            output_order = "F"

        return cls.from_coords(tuple(array.coords.values())[orderer], output_order)
