from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Variable(BaseModel):
    name: str
    unit: str
    description: Optional[str] = None

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str
    data_type: str
    spatial_coverage: Dict[str, Any]
    temporal_coverage: Dict[str, str]
    variables: List[Variable]
    file_format: str
    file_location: str

class DatasetCreate(DatasetBase):
    pass

class Dataset(DatasetBase):
    id: str

class DatasetListItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    file_location: str
