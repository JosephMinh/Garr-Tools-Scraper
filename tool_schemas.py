from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class ValidationStatus(str, Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"


class DrillAttributes(BaseModel):
    """Typed structure for drill-specific attributes"""

    point_angle_deg: Optional[float] = None
    xD: Optional[float] = None  # e.g., 5xD → 5.0
    coolant_through: Optional[bool] = None
    self_centering: Optional[bool] = None
    near_reamer_finish: Optional[bool] = None
    drill_category: Optional[Literal["high_performance", "general_purpose"]] = None
    neck_diameter: Optional[float] = None
    neck_length: Optional[float] = None


class EndMillAttributes(BaseModel):
    """Typed structure for end mill-specific attributes"""

    end_type: Optional[Literal["flat", "ball", "bullnose", "chamfer", "unknown"]] = None
    corner_radius_mm: Optional[float] = None
    helix_angle_deg: Optional[float] = None
    neck_diameter_mm: Optional[float] = None
    neck_length_mm: Optional[float] = None
    center_cutting: Optional[bool] = None
    reduced_shank: Optional[bool] = None


class ReamerAttributes(BaseModel):
    """Typed structure for reamer-specific attributes"""

    flute_style: Optional[Literal["straight", "spiral"]] = None
    tolerance_class: Optional[str] = None  # "H7", "H8", or explicit
    lead_in_length: Optional[float] = None
    chamfer_length: Optional[float] = None
    coolant_through: Optional[bool] = None


class DrillMillAttributes(BaseModel):
    """Typed structure for drill mill-specific attributes"""

    point_angle_deg: Optional[float] = None
    center_cutting: Optional[bool] = None


class RougherAttributes(BaseModel):
    """Typed structure for rougher-specific attributes"""

    chipbreaker_style: Optional[str] = None
    serration_note: Optional[str] = None
    rougher_profile_note: Optional[str] = None


class BurrAttributes(BaseModel):
    """Typed structure for burr/rotary file-specific attributes"""

    head_shape: Optional[str] = None
    cut_style: Optional[Literal["single_cut", "double_cut"]] = None
    head_diameter_mm: Optional[float] = None
    head_length_mm: Optional[float] = None


# ===== Helper structure for attributes_json =====
class ToolAttributesStructure(BaseModel):
    """
    Suggested structure for attributes_json content.
    This is NOT enforced by the Tool model, just documentation.
    """

    # Parsed tool-specific attributes (use appropriate *Attributes model)
    drill: Optional[DrillAttributes] = None
    end_mill: Optional[EndMillAttributes] = None
    reamer: Optional[ReamerAttributes] = None
    drill_mill: Optional[DrillMillAttributes] = None
    rougher: Optional[RougherAttributes] = None
    burr: Optional[BurrAttributes] = None

    # Raw unparseable fields
    raw_field_keys: Optional[str] = Field(
        None,
        description="Comma-separated list of field names that were present but couldn't be parsed reliably",
    )


class Tool(BaseModel):
    # ===== Identity =====
    vendor_name: str = Field(default="GARR", description="Vendor name")
    vendor_product_id: str = Field(..., description="EDP number")
    series_name: Optional[str] = Field(None, description="Tool series")
    tool_name: Optional[str] = Field(None, description="Page title string")
    xD: Optional[float] = Field(
        None, description="Drill length multiple, e.g., 5.0 for 5xD"
    )
    # product_url: HttpUrl = Field(..., description="URL of the product page")

    # # ===== Core geometry/metadata (common across most tools) =====
    # diameter: Optional[float] = Field(None, description="Tool diameter in specified units")
    # flute_count: Optional[int] = Field(None, description="Number of flutes")
    # flute_length: Optional[float] = Field(None, description="Length of flutes")
    # shank_diameter: Optional[float] = Field(None, description="Shank diameter")
    # reach_length: Optional[float] = Field(None, description="Reach length if present")
    # overall_length: Optional[float] = Field(None, description="Overall tool length")
    # coating: Optional[str] = Field(None, description="Tool coating type")
    # tool_material: Optional[str] = Field(None, description="Material of the tool")

    # # Tolerances as structured data
    # tolerance_diameter: Optional[str] = Field(
    #     None,
    #     description="Diameter tolerance (e.g., '+0.000/-0.001')"
    # )
    # tolerance_length: Optional[str] = Field(
    #     None,
    #     description="Length tolerance (e.g., '±0.010')"
    # )

    # # ===== Traceability =====
    # scrape_timestamp_utc: datetime = Field(
    #     default_factory=datetime.utcnow,
    #     description="UTC timestamp when scraped"
    # )
    # source_html_hash: str = Field(..., description="SHA256 hash of source HTML")

    # # ===== Validation Status =====
    # validation_status: ValidationStatus = Field(
    #     default=ValidationStatus.OK,
    #     description="Parsing validation status"
    # )
    # validation_notes: Optional[str] = Field(
    #     None,
    #     description="Notes about parsing issues or warnings"
    # )

    # # ===== Tool-specific attributes =====
    # drill_attributes: Optional[DrillAttributes] = Field(
    #     default=None,
    #     description="Drill-specific attributes if applicable"
    # )
    # end_mill_attributes: Optional[EndMillAttributes] = Field(
    #     default=None,
    #     description="End mill-specific attributes if applicable"
    # )
    # reamer_attributes: Optional[ReamerAttributes] = Field(
    #     default=None,
    #     description="Reamer-specific attributes if applicable"
    # )
    # drill_mill_attributes: Optional[DrillMillAttributes] = Field(
    #     default=None,
    #     description="Drill mill-specific attributes if applicable"
    # )
    # rougher_attributes: Optional[RougherAttributes] = Field(
    #     default=None,
    #     description="Rougher-specific attributes if applicable"
    # )
    # burr_attributes: Optional[BurrAttributes] = Field(
    #     default=None,
    #     description="Burr/rotary file-specific attributes if applicable"
    # )

    # class Config:
    #     use_enum_values = True


class Series(BaseModel):
    name: str
    details: Optional[str] = None
    tolerances: Optional[str] = None
    tools: list[Tool] = []


class ProductType(BaseModel):
    name: str
    series: list[Series] = []


class Products(BaseModel):
    types: list[ProductType] = []
