
from pydantic import BaseModel, Field, HttpUrl
from pydantic.types import conlist, Json
from pydantic import BaseModel, validator, ValidationError, model_validator, field_validator, field_serializer, model_serializer, computed_field, ValidationError,ValidationInfo
import json
from typing import Any, Dict, List, Optional, Union, Tuple, Type
from functools import wraps
import datetime
import re
import inspect
from enum import Enum
import xml.etree.ElementTree as ET

pricing_data = {
    "anthropic": {
      "claude-3-opus-20240229": {
        "input_price": "15.00",
        "output_price": "75.00",
        "context_window": 200000,
        "RPM": 2000,
        "TPM": 100000
      },
      "claude-3-sonnet-20240229": {
        "input_price": "3.00",
        "output_price": "15.00",
        "context_window": 200000,
        "RPM": 2000,
        "TPM": 100000
      },
      "claude-3-haiku-20240307": {
        "input_price": "0.25",
        "output_price": "1.25",
        "context_window": 200000,
        "RPM": 2000,
        "TPM": 100000
      }
    },
    "openai": {
        "gpt-4o": {
      "input_price": "2.50",
      "output_price": "10.00",
      "TPM": 30000000,
      "RPM": 10000,
      "context_window": 128000
    },
      "gpt-4-turbo": {
        "input_price": "10.00",
        "output_price": "30.00",
        "TPM": 800000,
        "RPM": 10000,
        "context_window": 128000
      },
      "gpt-4-0125-preview": {
        "input_price": "10.00",
        "output_price": "30.00",
        "TPM": 800000,
        "RPM": 10000,
        "context_window": 128000
      },
      "gpt-4-1106-preview": {
        "input_price": "10.00",
        "output_price": "30.00",
        "TPM": 800000,
        "RPM": 10000,
        "context_window": 128000
      },
      "gpt-4-1106-vision-preview": {
        "input_price": "10.00",
        "output_price": "30.00",
        "TPM": 150000,
        "RPM": 300000
      },
      "gpt-4": {
        "input_price": "30.00",
        "output_price": "60.00",
        "TPM": 300000,
        "RPM": 10000,
        "context_window": 8192
      },
      "gpt-4-32k": {
        "input_price": "60.00",
        "output_price": "120.00"
      },
      "gpt-3.5-turbo": {
        "input_price": "0.50",
        "output_price": "1.50",
        "TPM": 1000000,
        "RPM": 10000,
        "context_window": 16385
      },
      "gpt-3.5-turbo-0125": {
        "input_price": "0.50",
        "output_price": "1.50",
        "TPM": 1000000,
        "RPM": 10000,
        "context_window": 16385
      },
      "gpt-3.5-turbo-1106": {
        "input_price": "1.00",
        "output_price": "2.00",
        "TPM": 1000000,
        "RPM": 10000,
        "context_window": 16385
      },
      "gpt-3.5-turbo-0301": {
        "input_price": "1.50",
        "output_price": "2.00",
        "TPM": 1000000,
        "RPM": 10000
      },
      "gpt-3.5-turbo-0613": {
        "input_price": "1.50",
        "output_price": "2.00",
        "TPM": 1000000,
        "RPM": 10000
      },
      "gpt-3.5-turbo-instruct": {
        "input_price": "1.50",
        "output_price": "2.00",
        "TPM": 90000,
        "RPM": 3500,
        "context_window": 4096
      },
      "gpt-3.5-turbo-16k": {
        "input_price": "3.00",
        "output_price": "4.00",
        "TPM": 1000000,
        "RPM": 10000,
        "context_window": 16385
      },
      "gpt-3.5-turbo-16k-0613": {
        "input_price": "3.00",
        "output_price": "4.00",
        "TPM": 1000000,
        "RPM": 10000,
        "context_window": 16385
      },
      "text-embedding-3-small": {
        "input_price": "0.02",
        "output_price": "",
        "TPM": 5000000,
        "RPM": 10000
      },
      "text-embedding-3-large": {
        "input_price": "0.13",
        "output_price": "",
        "TPM": 5000000,
        "RPM": 10000
      },
      "text-embedding-ada-002": {
        "input_price": "0.10",
        "output_price": "",
        "TPM": 5000000,
        "RPM": 10000
      },
      "davinci-002": {
        "input_price": "12.00",
        "output_price": "12.00",
        "TPM": 250000,
        "RPM": 3000,
        "context_window": 16384
      },
      "babbage-002": {
        "input_price": "1.60",
        "output_price": "1.60",
        "TPM": 250000,
        "RPM": 3000,
        "context_window": 16384
      }
    }
  }



from pydantic import BaseModel, Field, HttpUrl
from pydantic.types import conlist, Json
from pydantic import BaseModel, validator, ValidationError, model_validator, field_validator, field_serializer, model_serializer, computed_field, root_validator, ValidationError,ValidationInfo
from typing import Optional, Dict, Any, List
import datetime

class Jurisdiction(BaseModel):
    name: str = Field(description="Name for the jurisdiction")
    iso: str = Field(description="ISO of the jurisdiction")
    type: str = Field(description="Country or state")
    parent_iso: Optional[str] = Field(default=None, description="iso of the parent jurisdiction, if any")


class Category(BaseModel):
    name: str = Field(description="Name for the category")
    id: int = Field(description="ID for the category")

class SubCategory(BaseModel):
    name: str = Field(description="Name for the SubCategory")
    id: str = Field(description="ID for the SubCategory")

class RecordType(BaseModel):
	name: str
	id: str

class Citation(BaseModel):
    id: str
    fk_id: str # represented as 'no' in API
    category: str
    subcategory: str
    record_type: str
    who: str
    what_to_store: str
    minimum_or_maximum: str
    retention: int
    period: str
    calculated_period: Optional[float] = Field(default=None, description="Retention period converted to years for standardization")
    from_date: str # represented as 'from' in API
    legal_reference: str
    link_legal_reference: str
    created_at: Optional[datetime.datetime] = Field(default=datetime.datetime.now(), description="Timestamp of when the citation was created in the system")
    updated_at: Optional[datetime.datetime] = Field(default=datetime.datetime.now(), description="Timestamp of the last update to the citation")

    jurisdiction_id: Optional[str] = Field(default=None, description="ID of the jurisdiction, standalone")
    category_id: Optional[str] = Field(default=None, description="ID of the category, standalone")
    subcategory_id: Optional[str] = Field(default=None, description="ID of the subcategory, composite ID")
    record_type_id: Optional[str] = Field(default=None, description="ID of the record type, composite ID")
    citation_id: Optional[str] = Field(default=None, description="ID of the citation, composite ID")








def main():
    # test_link = "https://www.ecfr.gov/current/title-40/part-205/subpart-s"
    # analyze_partial_link(test_link, "will2")
    pass
    # test_id = "us/federal/ecfr/title=7/subtitle=B/chapter=XI/part=1219/subpart=A/subject-group=ECFR70215de6cdda424/section=1219.54"
    # sql_select = f"SELECT * FROM us_federal_ecfr WHERE id = '{test_id}';"
    # row: Node = util.pydantic_select(sql_select, classType=Node, user="will2")[0]
    # all_definitions = fetch_definitions("will2", node_id=test_id)
    

    # definition_dict = all_definitions[0][1]
    # with open("test_definitions.json", "w") as file:
    #     json.dump(definition_dict, file, indent=4)
    # file.close()
    # node_text = row.node_text.to_list_text()

    # print(f"Node Text: {node_text}")
    # filtered_definitions = filter_definitions_from_node_text(node_text, definition_dict)
    
    # print(f"Filtered Definitions: {filtered_definitions.keys()}")





ALLOWED_LEVELS = [
    "title",
    "subtitle",
    "code",
    "part",
    "subpart",
    "division",
    "subdivision",
    "article",
    "subarticle",
    "chapter",
    "subchapter",
    "subject-group",
    "section",
    "appendix",
    "hub"
]

if __name__ == "__main__":
    main()


