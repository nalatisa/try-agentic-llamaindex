# models.py
# struktur json untuk validasi
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class ColumnRef(BaseModel):
    type: Literal["column"] = "column"
    source_id: str
    table: str
    column: str


class LiteralExpr(BaseModel):
    type: Literal["literal"] = "literal"
    value: Any


class SelectItem(BaseModel):
    expr: Any
    alias: Optional[str] = None


class FromClause(BaseModel):
    source_id: str
    table: str


class IRQuery(BaseModel):
    select: List[SelectItem]
    from_: FromClause = Field(..., alias="from")
    joins: Optional[List[Any]] = None
    where: Optional[Any] = None
    having: Optional[Any] = None
    group_by: Optional[List[ColumnRef]] = None
    order_by: Optional[List[Any]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
