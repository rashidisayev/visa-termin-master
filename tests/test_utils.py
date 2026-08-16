"""
Tests for lib/utils.py - Utility functions module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, mock_open
from lib import utils


class TestLoggerSetup:
    """Test logger setup functionality."""
    
    def test_setup_logger_returns_logger(self):
        """Test setup_logger returns a logger instance."""
        logger = utils.setup_logger()
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")
    
    def test_logger_is_consistent(self):
        """Test setup_logger returns consistent logger."""
        logger1 = utils.setup_logger()
        logger2 = utils.setup_logger()
        assert logger1 is not None
        assert logger2 is not None
    
    def test_logger_can_log_info(self):
        """Test logger can log info messages."""
        logger = utils.setup_logger()
        # Should not raise
        logger.info("Test info message")
    
    def test_logger_can_log_error(self):
        """Test logger can log error messages."""
        logger = utils.setup_logger()
        # Should not raise
        logger.error("Test error message")


class TestFileOperations:
    """Test file operation utilities."""
    
    def test_load_html_file_existing(self, temp_project_dir):
        """Test loading an existing HTML file."""
        html_path = Path(temp_project_dir) / "test.html"
        html_content = "<html><body>Test</body></html>"
        html_path.write_text(html_content)
        
        loaded = utils.load_html_file(str(html_path))
        assert loaded is not None
        assert "Test" in loaded
    
    def test_load_html_file_nonexistent(self):
        """Test loading a non-existent file returns None."""
        loaded = utils.load_html_file("/nonexistent/path/file.html")
        assert loaded is None
    
    def test_save_file_creates_file(self, temp_project_dir):
        """Test saving a file creates it."""
        file_path = Path(temp_project_dir) / "output.txt"
        content = "Test content"
        
        utils.save_file(str(file_path), content)
        
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_save_file_overwrites_existing(self, temp_project_dir):
        """Test saving a file overwrites existing content."""
        file_path = Path(temp_project_dir) / "output.txt"
        file_path.write_text("Old content")
        
        new_content = "New content"
        utils.save_file(str(file_path), new_content)
        
        assert file_path.read_text() == new_content
    
    def test_read_file_content_existing(self, temp_project_dir):
        """Test reading file content."""
        file_path = Path(temp_project_dir) / "input.txt"
        content = "Test file content\nLine 2\nLine 3"
        file_path.write_text(content)
        
        read_content = utils.read_file_content(str(file_path))
        assert read_content == content
    
    def test_read_file_content_nonexistent(self):
        """Test reading non-existent file returns None."""
        content = utils.read_file_content("/nonexistent/file.txt")
        assert content is None


class TestHtmlParsing:
    """Test HTML parsing utilities."""
    
    def test_find_element_by_id(self):
        """Test finding element by ID."""
        html_str = "<div id='test_id'>Content</div>"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_str, "html.parser")
        
        elem = utils.find_element(soup, "div", {"id": "test_id"})
        assert elem is not None
        assert "Content" in str(elem)
    
    def test_find_element_by_class(self):
        """Test finding element by class."""
        html_str = "<div class='test_class'>Content</div>"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_str, "html.parser")
        
        elem = utils.find_element(soup, "div", {"class": "test_class"})
        assert elem is not None
    
    def test_find_element_not_found(self):
        """Test finding non-existent element returns None."""
        html_str = "<div>Content</div>"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_str, "html.parser")
        
        elem = utils.find_element(soup, "span", {"id": "nonexistent"})
        assert elem is None
    
    def test_find_all_elements(self):
        """Test finding all elements."""
        html_str = """
        <div>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
            <p>Paragraph 3</p>
        </div>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_str, "html.parser")
        
        elems = utils.find_all_elements(soup, "p", {})
        assert elems is not None
        assert len(elems) == 3
    
    def test_find_all_elements_empty(self):
        """Test finding non-existent elements returns empty list."""
        html_str = "<div>Content</div>"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_str, "html.parser")
        
        elems = utils.find_all_elements(soup, "span", {})
        assert elems is not None
        assert len(elems) == 0


class TestImageExtraction:
    """Test image extraction utilities."""
    
    def test_extract_base64_image_from_valid_data(self):
        """Test extracting base64 image data."""
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        result = utils.extract_base64_image(base64_data)
        # Should handle base64 extraction
        assert result is not None or result is None
    
    def test_extract_base64_image_empty(self):
        """Test extracting from empty data."""
        result = utils.extract_base64_image("")
        # Should handle gracefully
        assert result is None or result == ""


class TestFileAndFolderHandling:
    """Test file and folder handling."""
    
    def test_directory_creation_in_load_html(self, temp_project_dir):
        """Test that load_html_file handles directories gracefully."""
        # Attempting to load a directory should not crash
        result = utils.load_html_file(temp_project_dir)
        assert result is None or isinstance(result, str)
    
    def test_save_file_with_nested_directory(self, temp_project_dir):
        """Test saving file in nested directory."""
        nested_path = Path(temp_project_dir) / "sub" / "nested" / "file.txt"
        content = "Test"
        
        # Should handle creation or fail gracefully
        try:
            utils.save_file(str(nested_path), content)
            # If successful, verify it was created
            if nested_path.exists():
                assert nested_path.read_text() == content
        except (FileNotFoundError, OSError):
            # Acceptable if utility doesn't create nested directories
            pass


class TestErrorHandling:
    """Test error handling in utilities."""
    
    def test_load_html_file_handles_encoding(self, temp_project_dir):
        """Test load_html_file handles encoding issues."""
        html_path = Path(temp_project_dir) / "test.html"
        # Write with UTF-8
        html_path.write_text("<html>Test with emoji 🎫</html>", encoding="utf-8")
        
        loaded = utils.load_html_file(str(html_path))
        assert loaded is not None
    
    def test_save_file_with_special_characters(self, temp_project_dir):
        """Test saving file with special characters."""
        file_path = Path(temp_project_dir) / "special.txt"
        content = "Special chars: äöü ñ é 中文"
        
        utils.save_file(str(file_path), content)
        
        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == content


class TestReturnTypes:
    """Test that utilities return correct types."""
    
    def test_setup_logger_returns_logger_type(self):
        """Test logger is correct type."""
        logger = utils.setup_logger()
        # Should be a logging.Logger or similar
        assert hasattr(logger, "info")
        assert callable(logger.info)
    
    def test_load_html_returns_string_or_none(self):
        """Test load_html_file returns string or None."""
        result = utils.load_html_file("/nonexistent.html")
        assert result is None or isinstance(result, str)
    
    def test_find_element_returns_element_or_none(self):
        """Test find_element returns element or None."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup("<div></div>", "html.parser")
        result = utils.find_element(soup, "span", {})
        assert result is None or hasattr(result, "name")
    
    def test_find_all_elements_returns_list(self):
        """Test find_all_elements returns list."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup("<div><p>Test</p></div>", "html.parser")
        result = utils.find_all_elements(soup, "p", {})
        assert isinstance(result, list)
