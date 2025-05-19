import uuid
import json
import os
from typing import List, Dict, Optional
from app.schemas.dataset import Dataset, DatasetCreate, DatasetListItem

DATASET_DB = "backend/docker/datasets/datasets.json"

def _load_db() -> List[Dict]:
    if not os.path.exists(DATASET_DB):
        return []
    with open(DATASET_DB, "r") as f:
        return json.load(f)

def _save_db(data: List[Dict]):
    os.makedirs(os.path.dirname(DATASET_DB), exist_ok=True)
    with open(DATASET_DB, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_datasets() -> List[DatasetListItem]:
    return [DatasetListItem(**d) for d in _load_db()]

def get_dataset(dataset_id: str) -> Optional[Dataset]:
    for d in _load_db():
        if d["id"] == dataset_id:
            return Dataset(**d)
    return None

def create_dataset(data: DatasetCreate) -> Dataset:
    db = _load_db()
    new_id = str(uuid.uuid4())
    item = data.dict()
    item["id"] = new_id
    db.append(item)
    _save_db(db)
    return Dataset(**item)

def delete_dataset(dataset_id: str) -> bool:
    db = _load_db()
    new_db = [d for d in db if d["id"] != dataset_id]
    if len(new_db) == len(db):
        return False
    _save_db(new_db)
    return True
