# dummy_api.py
from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Dummy DWH Schema API")


class ColumnInfo(BaseModel):
    name: str
    type: str


class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]


class SourceSchema(BaseModel):
    source_id: str
    provider: str
    tables: List[TableInfo]


def build_tables():
    return [
        TableInfo(
            name="dim_brand",
            columns=[
                ColumnInfo(name="brand_id", type="integer"),
                ColumnInfo(name="brand_name", type="string"),
            ],
        ),
        TableInfo(
            name="dim_category",
            columns=[
                ColumnInfo(name="category_id", type="integer"),
                ColumnInfo(name="parent_category_id", type="float"),
                ColumnInfo(name="category_name", type="string"),
            ],
        ),
        TableInfo(
            name="dim_channel",
            columns=[
                ColumnInfo(name="channel_id", type="integer"),
                ColumnInfo(name="channel_name", type="string"),
            ],
        ),
        TableInfo(
            name="dim_country",
            columns=[
                ColumnInfo(name="country_id", type="integer"),
                ColumnInfo(name="country_name", type="string"),
                ColumnInfo(name="continent", type="string"),
            ],
        ),
        TableInfo(
            name="dim_customer",
            columns=[
                ColumnInfo(name="customer_id", type="integer"),
                ColumnInfo(name="customer_name", type="string"),
                ColumnInfo(name="segment_id", type="integer"),
                ColumnInfo(name="region_id", type="integer"),
                ColumnInfo(name="join_date", type="string"),
            ],
        ),
        TableInfo(
            name="dim_customer_segment",
            columns=[
                ColumnInfo(name="segment_id", type="integer"),
                ColumnInfo(name="segment_name", type="string"),
            ],
        ),
        TableInfo(
            name="dim_date",
            columns=[
                ColumnInfo(name="date_id", type="integer"),
                ColumnInfo(name="full_date", type="string"),
                ColumnInfo(name="day", type="integer"),
                ColumnInfo(name="month", type="integer"),
                ColumnInfo(name="year", type="integer"),
                ColumnInfo(name="quarter", type="string"),
            ],
        ),
        TableInfo(
            name="dim_product",
            columns=[
                ColumnInfo(name="product_id", type="integer"),
                ColumnInfo(name="product_name", type="string"),
                ColumnInfo(name="category_id", type="integer"),
                ColumnInfo(name="brand_id", type="integer"),
            ],
        ),
        TableInfo(
            name="dim_region",
            columns=[
                ColumnInfo(name="region_id", type="integer"),
                ColumnInfo(name="country_id", type="integer"),
                ColumnInfo(name="region_name", type="string"),
            ],
        ),
        TableInfo(
            name="dim_store",
            columns=[
                ColumnInfo(name="store_id", type="integer"),
                ColumnInfo(name="store_name", type="string"),
                ColumnInfo(name="region_id", type="integer"),
            ],
        ),
        TableInfo(
            name="fact_customer_interaction",
            columns=[
                ColumnInfo(name="interaction_id", type="integer"),
                ColumnInfo(name="customer_id", type="integer"),
                ColumnInfo(name="date_id", type="integer"),
                ColumnInfo(name="channel_id", type="integer"),
                ColumnInfo(name="interaction_type", type="string"),
                ColumnInfo(name="interaction_text", type="string"),
            ],
        ),
        TableInfo(
            name="fact_transaction",
            columns=[
                ColumnInfo(name="transaction_id", type="integer"),
                ColumnInfo(name="date_id", type="integer"),
                ColumnInfo(name="customer_id", type="integer"),
                ColumnInfo(name="product_id", type="integer"),
                ColumnInfo(name="store_id", type="integer"),
                ColumnInfo(name="channel_id", type="integer"),
                ColumnInfo(name="quantity", type="integer"),
                ColumnInfo(name="unit_price", type="integer"),
                ColumnInfo(name="discount_amount", type="integer"),
                ColumnInfo(name="total_amount", type="integer"),
                ColumnInfo(name="transaction_note", type="string"),
            ],
        ),
    ]


SCHEMAS: Dict[str, SourceSchema] = {
    "d4df49c4-0fcd-4145-b852-ff889d3e4842": SourceSchema(
        source_id="d4df49c4-0fcd-4145-b852-ff889d3e4842",
        provider="postgres",
        tables=build_tables(),
    ),
    "0ff6daa0-ac80-4e28-87b3-a7fd5cc8eb38": SourceSchema(
        source_id="0ff6daa0-ac80-4e28-87b3-a7fd5cc8eb38",
        provider="postgres",
        tables=build_tables(),
    ),
}


@app.get("/schema", response_model=SourceSchema)
async def get_schema(source_id: str):
    if source_id not in SCHEMAS:
        return {"error": "Source ID not found"}
    return SCHEMAS[source_id]


@app.get("/schemas")
async def get_all_schemas():
    return list(SCHEMAS.values())


# Jalankan:
# uvicorn dummy_api:app --reload
