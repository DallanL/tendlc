from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class BrandIdentity(BaseModel):
    name: str
    ein: str
    address: str
    website: HttpUrl

class CampaignDetails(BaseModel):
    use_case: str
    sample_messages: List[str]

class VettingResult(BaseModel):
    status: str  # "Approved" or "Rejected"
    feedback: str
    details: Optional[dict] = None
