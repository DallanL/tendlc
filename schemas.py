from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class BrandIdentity(BaseModel):
    legal_name: str
    dba_name: Optional[str] = None
    legal_form: str  # Government, Non-Profit, Private, Public
    country_of_registration: str
    ein: str
    tax_id_issuing_country: str
    alt_business_id_type: str  # DUNS, GIIN, LEI, N/A
    alt_business_id: Optional[str] = None
    address: str
    website_url: HttpUrl
    privacy_policy_url: HttpUrl
    terms_and_conditions_url: HttpUrl
    stock_symbol: Optional[str] = None
    stock_exchange: Optional[str] = None
    contact_first_name: str
    contact_last_name: str
    contact_email: str
    contact_phone: str


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
    description: str = Field(..., min_length=40, max_length=4000)
    cta_flow: str = Field(..., min_length=40, max_length=4000)
    sample_messages: List[str]
    embedded_link_sample: Optional[str] = Field(None, max_length=255)
    attributes: CampaignAttributes


class VettingResult(BaseModel):
    status: str  # "Approved" or "Rejected"
    feedback: str
    details: Optional[dict] = None
