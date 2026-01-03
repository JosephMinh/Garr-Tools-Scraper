from firecrawl import Firecrawl
from pydantic import BaseModel
from tool_schemas import Tool, Series, ProductType, Products
import os

app = Firecrawl(api_key=os.getenv("firecrawl_api"))

result = app.scrape(
    "https://www.garrtool.com/product-details/?EDP=70631",
    formats=[
        {
            "type": "json",
            "schema": Tool.model_json_schema(),
            "prompt": "Scrape all relevant fields for the tool on this page. Return a JSON object matching the Tool schema.",
        }
    ],
    only_main_content=False,
    timeout=120000,
)

print(result)


with open("garr_tools.json", "w", encoding="utf-8") as f:
    f.write(result.model_dump_json(indent=2))
