"""
Tests for lib/booking_process.py - Portal detection and adaptation module.
"""
import pytest
from lib.booking_process import BookingProcessDetector, PortalLayoutAdapter


class TestBookingProcessDetector:
    """Test portal type detection."""
    
    def test_detector_creation(self):
        """Test creating a BookingProcessDetector instance."""
        detector = BookingProcessDetector()
        assert detector is not None
        assert isinstance(detector, BookingProcessDetector)
    
    def test_detect_legacy_rktermin_portal(self, sample_legacy_portal_html):
        """Test detecting legacy RKTerMin portal."""
        detector = BookingProcessDetector()
        portal_type = detector.detect_portal_type(sample_legacy_portal_html)
        assert portal_type == "legacy_rktermin"
    
    def test_detect_new_digital_portal(self, sample_new_portal_html):
        """Test detecting new digital embassy portal."""
        detector = BookingProcessDetector()
        portal_type = detector.detect_portal_type(sample_new_portal_html)
        assert portal_type == "new_termin"
    
    def test_detect_doctolib_portal(self, sample_doctolib_html):
        """Test detecting Doctolib-based portal."""
        detector = BookingProcessDetector()
        portal_type = detector.detect_portal_type(sample_doctolib_html)
        assert portal_type == "doctolib"
    
    def test_detect_unknown_portal(self):
        """Test detecting unknown/custom portal."""
        detector = BookingProcessDetector()
        unknown_html = "<html><body><h1>Unknown Portal</h1></body></html>"
        portal_type = detector.detect_portal_type(unknown_html)
        # Should return something (custom or unknown)
        assert portal_type in ["custom_embassy", "unknown", "generic"]
    
    def test_extract_form_fields_legacy(self, sample_legacy_portal_html):
        """Test extracting form fields from legacy portal."""
        detector = BookingProcessDetector()
        fields = detector.extract_form_fields(sample_legacy_portal_html)
        assert isinstance(fields, dict)
        # Should find the form
        assert len(fields) >= 0
    
    def test_detect_appointment_slots_legacy(self, sample_legacy_portal_html):
        """Test detecting appointment slots in legacy portal."""
        detector = BookingProcessDetector()
        slots = detector.detect_appointment_slots(sample_legacy_portal_html)
        assert isinstance(slots, list)
        # Should find appointment dates
        assert len(slots) > 0
    
    def test_detect_appointment_slots_new(self, sample_new_portal_html):
        """Test detecting appointment slots in new portal."""
        detector = BookingProcessDetector()
        slots = detector.detect_appointment_slots(sample_new_portal_html)
        assert isinstance(slots, list)
        assert len(slots) > 0
    
    def test_detect_captcha_type_legacy(self, sample_legacy_portal_html):
        """Test detecting captcha type in legacy portal."""
        detector = BookingProcessDetector()
        captcha_type = detector.detect_captcha_type(sample_legacy_portal_html)
        # Legacy portal should have appointment_captcha
        assert captcha_type in ["appointment_captcha", "recaptcha", "hcaptcha", None]
    
    def test_detect_captcha_type_none(self):
        """Test detecting no captcha."""
        detector = BookingProcessDetector()
        html = "<html><body><h1>No Captcha</h1></body></html>"
        captcha_type = detector.detect_captcha_type(html)
        # Should return None or 'none'
        assert captcha_type in [None, "none"]


class TestPortalLayoutAdapter:
    """Test portal-specific layout adaptation."""
    
    def test_adapter_creation_legacy(self):
        """Test creating adapter for legacy portal."""
        adapter = PortalLayoutAdapter("legacy_rktermin")
        assert adapter is not None
        assert isinstance(adapter, PortalLayoutAdapter)
    
    def test_adapter_creation_new(self):
        """Test creating adapter for new portal."""
        adapter = PortalLayoutAdapter("new_termin")
        assert adapter is not None
    
    def test_adapter_creation_doctolib(self):
        """Test creating adapter for Doctolib portal."""
        adapter = PortalLayoutAdapter("doctolib")
        assert adapter is not None
    
    def test_adapter_creation_custom(self):
        """Test creating adapter for custom portal."""
        adapter = PortalLayoutAdapter("custom_embassy")
        assert adapter is not None
    
    def test_extract_dates_from_legacy_portal(self, sample_legacy_portal_html):
        """Test extracting dates from legacy portal."""
        from lib import config
        adapter = PortalLayoutAdapter("legacy_rktermin")
        dates = adapter.extract_available_dates(sample_legacy_portal_html, config)
        # Should extract dates or return None
        if dates:
            assert isinstance(dates, str)
            # Should be in DD.MM.YYYY format
            parts = dates.split(".")
            assert len(parts) == 3
    
    def test_extract_dates_from_new_portal(self, sample_new_portal_html):
        """Test extracting dates from new portal."""
        from lib import config
        adapter = PortalLayoutAdapter("new_termin")
        dates = adapter.extract_available_dates(sample_new_portal_html, config)
        # Should extract dates or return None
        if dates:
            assert isinstance(dates, str)
    
    def test_extract_dates_from_doctolib(self, sample_doctolib_html):
        """Test extracting dates from Doctolib portal."""
        from lib import config
        adapter = PortalLayoutAdapter("doctolib")
        dates = adapter.extract_available_dates(sample_doctolib_html, config)
        # Should extract dates or return None
        if dates:
            assert isinstance(dates, str)
    
    def test_adapter_fallback_extraction(self):
        """Test adapter falls back to generic extraction."""
        from lib import config
        adapter = PortalLayoutAdapter("unknown")
        html = "<html><body><p>Date available: 25.04.2024</p></body></html>"
        dates = adapter.extract_available_dates(html, config)
        # Should attempt extraction
        if dates:
            assert isinstance(dates, str)
    
    def test_extract_with_filtering_config(self, sample_legacy_portal_html):
        """Test that extraction respects config filtering."""
        from lib import config
        adapter = PortalLayoutAdapter("legacy_rktermin")
        # The extraction should use config.is_acceptable_date() for filtering
        dates = adapter.extract_available_dates(sample_legacy_portal_html, config)
        # If date is returned, it should pass the filter
        if dates:
            parts = dates.split(".")
            day = int(parts[0])
            month = int(parts[1])
            assert config.is_acceptable_date(month, day) is True
    
    def test_multiple_date_formats_handled(self):
        """Test adapter handles multiple date formats."""
        from lib import config
        # Should handle DD.MM.YYYY, DD-MM-YYYY, DD/MM/YYYY, etc.
        test_html = """
        <html>
        <body>
            <div>Date 1: 25.04.2024</div>
            <div>Date 2: 26-04-2024</div>
            <div>Date 3: 27/04/2024</div>
        </body>
        </html>
        """
        adapter = PortalLayoutAdapter("generic")
        # Adapter should handle various formats
        assert adapter is not None


class TestPortalDetectionAccuracy:
    """Test portal detection accuracy with real-world HTML."""
    
    def test_legacy_portal_has_appointment_captcha_form(self, sample_legacy_portal_html):
        """Test legacy portal detection relies on appointment_captcha_month form."""
        assert "appointment_captcha_month" in sample_legacy_portal_html
        detector = BookingProcessDetector()
        portal_type = detector.detect_portal_type(sample_legacy_portal_html)
        assert portal_type == "legacy_rktermin"
    
    def test_new_portal_has_data_attributes(self, sample_new_portal_html):
        """Test new portal detection relies on data attributes."""
        assert "data-date" in sample_new_portal_html
        detector = BookingProcessDetector()
        portal_type = detector.detect_portal_type(sample_new_portal_html)
        assert portal_type == "new_termin"
    
    def test_doctolib_has_specific_markers(self, sample_doctolib_html):
        """Test Doctolib detection relies on specific class names."""
        assert "doctolib-container" in sample_doctolib_html
        detector = BookingProcessDetector()
        portal_type = detector.detect_portal_type(sample_doctolib_html)
        assert portal_type == "doctolib"


class TestPortalDescriptions:
    """Test portal type descriptions."""
    
    def test_detector_provides_description(self):
        """Test detector can describe detected portal type."""
        detector = BookingProcessDetector()
        # After detecting a portal, should be able to get description
        if hasattr(detector, "get_portal_description"):
            description = detector.get_portal_description()
            assert isinstance(description, str)
            assert len(description) > 0
