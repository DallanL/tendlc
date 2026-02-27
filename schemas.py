from pydantic import BaseModel, Field
from typing import List, Optional


class CampaignAttributes(BaseModel):
    subscriber_opt_in: bool
    opt_in_keyword: Optional[str] = None
    opt_in_message: Optional[str] = None
    subscriber_opt_out: bool
    opt_out_keyword: Optional[str] = None
    opt_out_message: Optional[str] = None
    subscriber_help: bool
    help_keyword: Optional[str] = None
    help_message: Optional[str] = None
    number_pooling: bool
    direct_lending: bool
    embedded_link: bool
    embedded_phone: bool
    affiliate_marketing: bool
    age_gated: bool


class CampaignDetails(BaseModel):
    display_name: str
    vertical: str
    primary_use_case: str
    sub_use_cases: List[str] = []
    description: str = Field(..., min_length=40, max_length=4000)
    cta_flow: str = Field(..., min_length=40, max_length=4000)
    sample_messages: List[str]
    embedded_link_sample: Optional[str] = Field(None, max_length=255)
    attributes: CampaignAttributes
