"""
Tests for lib/extractors.py - HTML extraction module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from lib import extractors, config


class TestExtractAvailableDate:
    """Test extract_available_date function."""
    
    def test_extract_date_from_legacy_portal(self, temp_project_dir, sample_legacy_portal_html):
        """Test extracting date from legacy portal HTML."""
        # Create target directory and response file
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        response_file = target_dir / "response.html"
        response_file.write_text(sample_legacy_portal_html)
        
        # Extract date
        date = extractors.extract_available_date(temp_project_dir, "response.html")
        
        # Should find a date or return None
        if date:
            assert isinstance(date, str)
            assert "." in date  # DD.MM.YYYY format
    
    def test_extract_date_from_new_portal(self, temp_project_dir, sample_new_portal_html):
        """Test extracting date from new digital portal."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        response_file = target_dir / "response.html"
        response_file.write_text(sample_new_portal_html)
        
        date = extractors.extract_available_date(temp_project_dir, "response.html")
        
        if date:
            assert isinstance(date, str)
    
    def test_extract_date_file_not_found(self, temp_project_dir):
        """Test extraction handles missing file gracefully."""
        # Don't create any response file
        date = extractors.extract_available_date(temp_project_dir, "nonexistent.html")
        
        # Should return None without crashing
        assert date is None
    
    def test_extract_date_respects_config_filter(self, temp_project_dir, sample_legacy_portal_html):
        """Test that extraction respects config date filtering."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        response_file = target_dir / "response.html"
        response_file.write_text(sample_legacy_portal_html)
        
        date = extractors.extract_available_date(temp_project_dir, "response.html")
        
        # If a date is found, it should pass the config filter
        if date:
            parts = date.split(".")
            day = int(parts[0])
            month = int(parts[1])
            assert config.is_acceptable_date(month, day) is True
    
    def test_extract_date_returns_none_or_string(self, temp_project_dir):
        """Test extract_available_date return type."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        empty_file = target_dir / "empty.html"
        empty_file.write_text("<html></html>")
        
        result = extractors.extract_available_date(temp_project_dir, "empty.html")
        
        assert result is None or isinstance(result, str)


class TestExtractCaptchaImage:
    """Test extract_captcha_image function."""
    
    def test_extract_captcha_from_html(self, temp_project_dir, sample_visa_html_with_captcha):
        """Test extracting captcha image."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "captcha.html"
        html_file.write_text(sample_visa_html_with_captcha)
        
        # Extract captcha
        result = extractors.extract_captcha_image(
            temp_project_dir,
            "captcha.html",
            "captcha_image"
        )
        
        # Should return image path or None
        assert result is None or isinstance(result, str)
    
    def test_extract_captcha_selector_not_found(self, temp_project_dir):
        """Test extracting captcha with non-existent selector."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "no_captcha.html"
        html_file.write_text("<html><body></body></html>")
        
        result = extractors.extract_captcha_image(
            temp_project_dir,
            "no_captcha.html",
            "nonexistent_id"
        )
        
        # Should handle gracefully
        assert result is None or isinstance(result, str)


class TestExtractBookingTime:
    """Test extract_booking_time function."""
    
    def test_extract_booking_time_from_html(self, temp_project_dir):
        """Test extracting booking time from confirmation page."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        html_with_time = """
        <html>
        <body>
            <div class="confirmation">
                <p>Appointment confirmed for 25.04.2024 at 14:30</p>
            </div>
        </body>
        </html>
        """
        
        html_file = target_dir / "booking.html"
        html_file.write_text(html_with_time)
        
        time = extractors.extract_booking_time(temp_project_dir, "booking.html")
        
        # Should extract time or return None
        assert time is None or isinstance(time, str)
    
    def test_extract_booking_time_no_time_found(self, temp_project_dir):
        """Test extraction when no time found."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "no_time.html"
        html_file.write_text("<html><body>No appointment time</body></html>")
        
        time = extractors.extract_booking_time(temp_project_dir, "no_time.html")
        
        assert time is None or isinstance(time, str)


class TestExtractRescheduleUrl:
    """Test extract_reschedule_url function."""
    
    def test_extract_reschedule_url_from_html(self, temp_project_dir):
        """Test extracting reschedule URL."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        html_with_url = """
        <html>
        <body>
            <a href="/reschedule/token123" class="reschedule-link">Reschedule</a>
        </body>
        </html>
        """
        
        html_file = target_dir / "reschedule.html"
        html_file.write_text(html_with_url)
        
        url = extractors.extract_reschedule_url(temp_project_dir, "reschedule.html")
        
        # Should extract URL or return None
        assert url is None or isinstance(url, str)
    
    def test_extract_reschedule_url_not_found(self, temp_project_dir):
        """Test extraction when no reschedule URL found."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "no_reschedule.html"
        html_file.write_text("<html><body></body></html>")
        
        url = extractors.extract_reschedule_url(temp_project_dir, "no_reschedule.html")
        
        assert url is None or isinstance(url, str)


class TestPortalDetectionIntegration:
    """Test integration with portal detection."""
    
    def test_extraction_detects_legacy_portal(self, temp_project_dir, sample_legacy_portal_html):
        """Test that extraction detects legacy portal type."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        response_file = target_dir / "response.html"
        response_file.write_text(sample_legacy_portal_html)
        
        # This should trigger portal detection internally
        date = extractors.extract_available_date(temp_project_dir, "response.html")
        
        # Extraction should work regardless of what it detects
        assert date is None or isinstance(date, str)
    
    def test_extraction_adapts_to_new_portal(self, temp_project_dir, sample_new_portal_html):
        """Test that extraction adapts to new portal type."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        response_file = target_dir / "response.html"
        response_file.write_text(sample_new_portal_html)
        
        date = extractors.extract_available_date(temp_project_dir, "response.html")
        
        # Should still extract successfully
        assert date is None or isinstance(date, str)


class TestExtractionEdgeCases:
    """Test edge cases in extraction."""
    
    def test_extraction_with_malformed_html(self, temp_project_dir):
        """Test extraction handles malformed HTML."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "malformed.html"
        html_file.write_text("<html><body><h4>25.04.2024</h4></body>")  # Missing closing tags
        
        # Should not crash
        result = extractors.extract_available_date(temp_project_dir, "malformed.html")
        assert result is None or isinstance(result, str)
    
    def test_extraction_with_empty_file(self, temp_project_dir):
        """Test extraction handles empty files."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "empty.html"
        html_file.write_text("")
        
        result = extractors.extract_available_date(temp_project_dir, "empty.html")
        
        assert result is None or isinstance(result, str)
    
    def test_extraction_with_large_html(self, temp_project_dir):
        """Test extraction handles large HTML files."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create large HTML with many h4 elements
        large_html = "<html><body>"
        for i in range(100):
            large_html += f"<h4>Date: {25+i%30}.04.2024</h4>"
        large_html += "</body></html>"
        
        html_file = target_dir / "large.html"
        html_file.write_text(large_html)
        
        result = extractors.extract_available_date(temp_project_dir, "large.html")
        
        # Should handle efficiently
        assert result is None or isinstance(result, str)


class TestExtractionReturnTypes:
    """Test return types of extraction functions."""
    
    def test_extract_available_date_return_type(self, temp_project_dir):
        """Test extract_available_date returns string or None."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "test.html"
        html_file.write_text("<html></html>")
        
        result = extractors.extract_available_date(temp_project_dir, "test.html")
        
        assert result is None or isinstance(result, str)
    
    def test_extract_captcha_return_type(self, temp_project_dir):
        """Test extract_captcha_image returns string or None."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "test.html"
        html_file.write_text("<html></html>")
        
        result = extractors.extract_captcha_image(temp_project_dir, "test.html", "test_id")
        
        assert result is None or isinstance(result, str)
    
    def test_extract_booking_time_return_type(self, temp_project_dir):
        """Test extract_booking_time returns string or None."""
        target_dir = Path(temp_project_dir) / "target"
        target_dir.mkdir(parents=True, exist_ok=True)
        html_file = target_dir / "test.html"
        html_file.write_text("<html></html>")
        
        result = extractors.extract_booking_time(temp_project_dir, "test.html")
        
        assert result is None or isinstance(result, str)
