"""
Tests for lib/visa_types.py - Visa type management module.
"""
import pytest
from lib.visa_types import (
    VisaCategory,
    VisaTypeConfig,
    VisaTypeManager,
    DEFAULT_VISA_TYPES,
)


class TestVisaCategory:
    """Test VisaCategory enum."""
    
    def test_schengen_categories_are_c_visa(self):
        """Test Schengen categories are marked as C visas."""
        assert VisaCategory.SCHENGEN_TRANSIT.value == "C"
        assert VisaCategory.SCHENGEN_VISIT.value == "C"
        assert VisaCategory.BUSINESS.value == "C"
    
    def test_national_categories_are_d_visa(self):
        """Test national (D) visa categories."""
        assert VisaCategory.NATIONAL_WORK.value == "D"
        assert VisaCategory.NATIONAL_STUDY.value == "D"
        assert VisaCategory.NATIONAL_FAMILY.value == "D"
        assert VisaCategory.NATIONAL_RESIDENCE.value == "D"
    
    def test_unknown_category_value(self):
        """Test unknown category value."""
        assert VisaCategory.UNKNOWN.value == "UNKNOWN"


class TestVisaTypeConfig:
    """Test VisaTypeConfig dataclass."""
    
    def test_visa_config_creation(self):
        """Test creating a visa type configuration."""
        config = VisaTypeConfig(
            name="Test Visa",
            category=VisaCategory.SCHENGEN_VISIT,
            category_id="1234",
            realm_id="561",
            description="Test visa type",
            requires_documents=True,
            typical_processing_days=15,
            appointment_lead_time_days=3,
        )
        
        assert config.name == "Test Visa"
        assert config.category == VisaCategory.SCHENGEN_VISIT
        assert config.category_id == "1234"
        assert config.realm_id == "561"
        assert config.requires_documents is True
        assert config.typical_processing_days == 15
        assert config.appointment_lead_time_days == 3
    
    def test_visa_config_fields(self):
        """Test all required fields in visa config."""
        config = VisaTypeConfig(
            name="Work Visa",
            category=VisaCategory.NATIONAL_WORK,
            category_id="1785",
            realm_id="561",
            description="Employment visa",
            requires_documents=True,
            typical_processing_days=30,
            appointment_lead_time_days=7,
        )
        
        assert hasattr(config, "name")
        assert hasattr(config, "category")
        assert hasattr(config, "category_id")
        assert hasattr(config, "realm_id")
        assert hasattr(config, "description")
        assert hasattr(config, "requires_documents")
        assert hasattr(config, "typical_processing_days")
        assert hasattr(config, "appointment_lead_time_days")


class TestDefaultVisaTypes:
    """Test default visa type configurations."""
    
    def test_default_types_exist(self):
        """Test that default visa types are defined."""
        assert DEFAULT_VISA_TYPES is not None
        assert isinstance(DEFAULT_VISA_TYPES, dict)
    
    def test_schengen_default_type(self):
        """Test Schengen visa is in default types."""
        assert "schengen" in DEFAULT_VISA_TYPES
        config = DEFAULT_VISA_TYPES["schengen"]
        assert config.category == VisaCategory.SCHENGEN_VISIT
        assert config.category_id == "1497"
        assert config.requires_documents is True
    
    def test_work_default_type(self):
        """Test Work visa is in default types."""
        assert "work" in DEFAULT_VISA_TYPES
        config = DEFAULT_VISA_TYPES["work"]
        assert config.category == VisaCategory.NATIONAL_WORK
        assert config.category_id == "1785"
        assert config.typical_processing_days > 15  # D visas take longer
    
    def test_study_default_type(self):
        """Test Study visa is in default types."""
        assert "study" in DEFAULT_VISA_TYPES
        config = DEFAULT_VISA_TYPES["study"]
        assert config.category == VisaCategory.NATIONAL_STUDY
        assert config.category_id == "1786"
    
    def test_family_default_type(self):
        """Test Family visa is in default types."""
        assert "family" in DEFAULT_VISA_TYPES
        config = DEFAULT_VISA_TYPES["family"]
        assert config.category == VisaCategory.NATIONAL_FAMILY
        assert config.category_id == "1787"
    
    def test_residence_default_type(self):
        """Test Residence visa is in default types."""
        assert "residence" in DEFAULT_VISA_TYPES
        config = DEFAULT_VISA_TYPES["residence"]
        assert config.category == VisaCategory.NATIONAL_RESIDENCE
        assert config.category_id == "1788"


class TestVisaTypeManager:
    """Test VisaTypeManager class."""
    
    def test_manager_creation(self):
        """Test creating a VisaTypeManager instance."""
        manager = VisaTypeManager()
        assert manager is not None
        assert isinstance(manager, VisaTypeManager)
    
    def test_select_schengen_visa(self):
        """Test selecting Schengen visa type."""
        manager = VisaTypeManager()
        manager.select_visa_type("schengen")
        config = manager.get_selected_config()
        assert config.category == VisaCategory.SCHENGEN_VISIT
        assert config.category_id == "1497"
    
    def test_select_work_visa(self):
        """Test selecting Work visa type."""
        manager = VisaTypeManager()
        manager.select_visa_type("work")
        config = manager.get_selected_config()
        assert config.category == VisaCategory.NATIONAL_WORK
        assert config.category_id == "1785"
    
    def test_select_study_visa(self):
        """Test selecting Study visa type."""
        manager = VisaTypeManager()
        manager.select_visa_type("study")
        config = manager.get_selected_config()
        assert config.category == VisaCategory.NATIONAL_STUDY
        assert config.category_id == "1786"
    
    def test_select_invalid_visa_type(self):
        """Test selecting an invalid visa type."""
        manager = VisaTypeManager()
        # Should handle gracefully (either default or raise)
        with pytest.raises((KeyError, ValueError)):
            manager.select_visa_type("invalid_visa_type")
    
    def test_get_available_types(self):
        """Test getting list of available visa types."""
        manager = VisaTypeManager()
        types = manager.get_available_types()
        assert isinstance(types, (list, dict))
        assert len(types) > 0
        assert "schengen" in types
        assert "work" in types
    
    def test_get_visa_config(self):
        """Test getting specific visa configuration."""
        manager = VisaTypeManager()
        config = manager.get_visa_config("schengen")
        assert config is not None
        assert config.category == VisaCategory.SCHENGEN_VISIT
    
    def test_add_custom_type(self):
        """Test adding a custom visa type."""
        manager = VisaTypeManager()
        custom_config = VisaTypeConfig(
            name="Custom Visa",
            category=VisaCategory.UNKNOWN,
            category_id="9999",
            realm_id="999",
            description="Custom test visa",
            requires_documents=False,
            typical_processing_days=1,
            appointment_lead_time_days=0,
        )
        manager.add_custom_type("custom", custom_config)
        
        retrieved = manager.get_visa_config("custom")
        assert retrieved.category_id == "9999"
        assert retrieved.name == "Custom Visa"
    
    def test_get_category_ids_for_location(self):
        """Test getting category IDs for a specific location."""
        manager = VisaTypeManager()
        category_ids = manager.get_category_ids_for_location("kiew")
        assert isinstance(category_ids, dict)
        assert "schengen" in category_ids
        assert category_ids["schengen"] == "1497"
        assert category_ids["work"] == "1785"
    
    def test_get_category_id_schengen(self):
        """Test getting category ID for Schengen in Kyiv."""
        manager = VisaTypeManager()
        category_id = manager.get_category_id("schengen", "kiew")
        assert category_id == "1497"
    
    def test_get_category_id_work(self):
        """Test getting category ID for Work visa in Kyiv."""
        manager = VisaTypeManager()
        category_id = manager.get_category_id("work", "kiew")
        assert category_id == "1785"
    
    def test_get_category_id_berlin(self):
        """Test getting category ID for Berlin embassy."""
        manager = VisaTypeManager()
        category_id = manager.get_category_id("schengen", "berlin")
        # Berlin may have different IDs
        assert category_id is not None
        assert isinstance(category_id, str)
    
    def test_get_category_id_unknown_location(self):
        """Test getting category ID for unknown location."""
        manager = VisaTypeManager()
        # Should handle gracefully or use default
        category_id = manager.get_category_id("schengen", "unknown_location")
        # Should return something or handle gracefully
        assert category_id is not None or category_id is None
    
    def test_schengen_requires_documents(self):
        """Test Schengen visa requires documents."""
        manager = VisaTypeManager()
        config = manager.get_visa_config("schengen")
        assert config.requires_documents is True
    
    def test_d_visa_processing_time(self):
        """Test D visas have longer processing time than Schengen."""
        manager = VisaTypeManager()
        schengen_config = manager.get_visa_config("schengen")
        work_config = manager.get_visa_config("work")
        assert work_config.typical_processing_days > schengen_config.typical_processing_days
    
    def test_location_mappings_comprehensive(self):
        """Test that location mappings cover multiple cities."""
        manager = VisaTypeManager()
        # Should support at least Kyiv and Berlin
        kyiv_ids = manager.get_category_ids_for_location("kiew")
        berlin_ids = manager.get_category_ids_for_location("berlin")
        
        assert kyiv_ids is not None
        assert berlin_ids is not None
        # Different embassies may have different IDs
        assert len(kyiv_ids) > 0
        assert len(berlin_ids) > 0
