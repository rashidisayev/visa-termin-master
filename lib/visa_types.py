"""
Visa type definitions and management for German visa appointments.
Supports multiple visa categories: Schengen (C), National (D), and auto-detection.
"""
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


class VisaCategory(Enum):
    """German visa categories"""
    SCHENGEN_TRANSIT = "C"  # Transit visa
    SCHENGEN_VISIT = "C"    # Short-stay visitor
    BUSINESS = "C"           # Business visit
    NATIONAL_WORK = "D"      # Employment visa
    NATIONAL_STUDY = "D"     # Study visa
    NATIONAL_FAMILY = "D"    # Family reunion
    NATIONAL_SELF_EMPLOYED = "D"  # Freelancer/Self-employed
    NATIONAL_RESIDENCE = "D"  # General residence
    EU_RESIDENCE = "D"        # EU citizen family member
    UNKNOWN = "UNKNOWN"       # Auto-detect


@dataclass
class VisaTypeConfig:
    """Configuration for a specific visa type"""
    name: str
    category: VisaCategory
    category_id: str  # Consulate-specific category ID
    realm_id: str     # Consulate-specific realm ID
    description: str
    requires_documents: bool
    typical_processing_days: int
    appointment_lead_time_days: int
    

# Default German embassy visa category IDs (Kyiv example)
# These may vary by embassy location
DEFAULT_VISA_TYPES: Dict[str, VisaTypeConfig] = {
    "schengen": VisaTypeConfig(
        name="Schengen Visa",
        category=VisaCategory.SCHENGEN_VISIT,
        category_id="1497",
        realm_id="561",
        description="Schengen short-stay visa (up to 90 days)",
        requires_documents=True,
        typical_processing_days=15,
        appointment_lead_time_days=1,
    ),
    "work": VisaTypeConfig(
        name="Employment Visa (D)",
        category=VisaCategory.NATIONAL_WORK,
        category_id="1785",  # This may vary by embassy
        realm_id="561",
        description="National D visa for employment",
        requires_documents=True,
        typical_processing_days=30,
        appointment_lead_time_days=7,
    ),
    "study": VisaTypeConfig(
        name="Study Visa (D)",
        category=VisaCategory.NATIONAL_STUDY,
        category_id="1786",  # This may vary by embassy
        realm_id="561",
        description="National D visa for studies",
        requires_documents=True,
        typical_processing_days=30,
        appointment_lead_time_days=7,
    ),
    "family": VisaTypeConfig(
        name="Family Reunion Visa (D)",
        category=VisaCategory.NATIONAL_FAMILY,
        category_id="1787",  # This may vary by embassy
        realm_id="561",
        description="National D visa for family reunion",
        requires_documents=True,
        typical_processing_days=30,
        appointment_lead_time_days=7,
    ),
    "residence": VisaTypeConfig(
        name="Residence Permit (D)",
        category=VisaCategory.NATIONAL_RESIDENCE,
        category_id="1788",  # This may vary by embassy
        realm_id="561",
        description="National D visa for general residence",
        requires_documents=True,
        typical_processing_days=30,
        appointment_lead_time_days=7,
    ),
}


class VisaTypeManager:
    """Manages visa type configurations and selection"""
    
    def __init__(self):
        self.visa_types = DEFAULT_VISA_TYPES.copy()
        self.selected_type: Optional[str] = None
    
    def get_available_types(self) -> List[str]:
        """Get list of available visa type keys"""
        return list(self.visa_types.keys())
    
    def get_visa_config(self, visa_type: str) -> Optional[VisaTypeConfig]:
        """Get configuration for a specific visa type"""
        return self.visa_types.get(visa_type)
    
    def select_visa_type(self, visa_type: str) -> bool:
        """
        Select a visa type.
        
        Args:
            visa_type: Visa type key (e.g., 'schengen', 'work', 'study')
            
        Returns:
            True if valid type selected, False otherwise
        """
        if visa_type in self.visa_types:
            self.selected_type = visa_type
            return True
        return False
    
    def get_selected_config(self) -> Optional[VisaTypeConfig]:
        """Get configuration for currently selected visa type"""
        if not self.selected_type:
            return None
        return self.visa_types.get(self.selected_type)
    
    def add_custom_type(self, key: str, config: VisaTypeConfig) -> None:
        """
        Add a custom visa type configuration.
        
        Args:
            key: Unique identifier for the visa type
            config: VisaTypeConfig object with type details
        """
        self.visa_types[key] = config
    
    def get_category_ids_for_location(self, location: str) -> Dict[str, str]:
        """
        Get category IDs for a specific embassy location.
        This can be extended with location-specific mappings.
        
        Args:
            location: Embassy location code (e.g., 'kiew', 'berlin', 'moscow')
            
        Returns:
            Dictionary mapping visa type keys to category IDs
        """
        # Location-specific category ID overrides
        location_mappings = {
            "kiew": {
                "schengen": "1497",
                "work": "1785",
                "study": "1786",
                "family": "1787",
                "residence": "1788",
            },
            "berlin": {
                "schengen": "1401",
                "work": "1402",
                "study": "1403",
                "family": "1404",
                "residence": "1405",
            },
            "moscow": {
                "schengen": "1601",
                "work": "1602",
                "study": "1603",
                "family": "1604",
                "residence": "1605",
            },
        }
        
        return location_mappings.get(location, {
            key: config.category_id 
            for key, config in self.visa_types.items()
        })
    
    def get_category_id(self, visa_type: str, location: Optional[str] = None) -> Optional[str]:
        """
        Get category ID for a visa type at a specific location.
        
        Args:
            visa_type: Visa type key
            location: Embassy location (optional)
            
        Returns:
            Category ID or None if not found
        """
        if location:
            location_ids = self.get_category_ids_for_location(location)
            return location_ids.get(visa_type)
        
        config = self.get_visa_config(visa_type)
        return config.category_id if config else None
    
    def list_visa_types(self) -> str:
        """
        Get formatted list of available visa types.
        
        Returns:
            Formatted string with visa type information
        """
        output = "Available Visa Types:\n"
        output += "=" * 60 + "\n"
        
        for key, config in self.visa_types.items():
            output += f"\n{key.upper()}\n"
            output += f"  Name: {config.name}\n"
            output += f"  Category: {config.category.value}\n"
            output += f"  Description: {config.description}\n"
            output += f"  Processing Time: ~{config.typical_processing_days} days\n"
            output += f"  Lead Time: {config.appointment_lead_time_days} days\n"
        
        return output
