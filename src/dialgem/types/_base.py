"""The base every response model inherits from."""

from __future__ import annotations

from typing import Any, Dict, Union

from pydantic import BaseModel, ConfigDict

#: JSON has one number type. ``Union[int, float]`` keeps ``1730000000000`` an ``int``
#: instead of turning it into ``1730000000000.0``.
Number = Union[int, float]


class DialgemModel(BaseModel):
    """A response object.

    ``extra="allow"``: the API adds fields over time, and a client written last month must
    keep working. Unknown fields stay available as attributes and in ``model_extra``.
    ``populate_by_name`` lets a field whose wire name is not a Python identifier be set either way.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, protected_namespaces=())

    def to_dict(self) -> Dict[str, Any]:
        """The object as the API sent it (wire names, unknown fields included)."""
        return self.model_dump(mode="json", by_alias=True)
