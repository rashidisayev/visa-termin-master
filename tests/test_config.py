"""
Tests for lib/config.py - Configuration management module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import sys


class TestConfigBasics:
    """Test basic configuration loading."""
    
    def test_root_folder_default(self):
        """Test ROOT_FOLDER defaults to current working directory."""
        # Save original value
        original_root = os.environ.get("ROOT_FOLDER")
        
        try:
            # Remove ROOT_FOLDER env var
            if "ROOT_FOLDER" in os.environ:
                del os.environ["ROOT_FOLDER"]
            
            # Reimport to test default
            if "lib.config" in sys.modules:
                del sys.modules["lib.config"]
            
            from lib import config
            
            # Should default to current working directory
            assert config.ROOT_FOLDER is not None
            assert isinstance(config.ROOT_FOLDER, str)
        finally:
            # Restore
            if original_root:
                os.environ["ROOT_FOLDER"] = original_root
    
    def test_root_folder_custom(self, temp_project_dir):
        """Test ROOT_FOLDER can be set via environment variable."""
        os.environ["ROOT_FOLDER"] = temp_project_dir
        
        # Reimport to test custom value
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.ROOT_FOLDER == temp_project_dir
    
    def test_target_and_log_folders_exist(self, temp_project_dir):
        """Test that target and log folders are created automatically."""
        os.environ["ROOT_FOLDER"] = temp_project_dir
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        
        assert Path(config.TARGET_FOLDER).exists()
        assert Path(config.LOG_FOLDER).exists()


class TestUniversalConfiguration:
    """Test universal configuration system for visa types and embassies."""
    
    def test_default_visa_type_is_schengen(self, mock_env_vars):
        """Test VISA_TYPE defaults to 'schengen'."""
        mock_env_vars()  # Clear env vars
        if "VISA_TYPE" in os.environ:
            del os.environ["VISA_TYPE"]
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.VISA_TYPE == "schengen"
    
    def test_visa_type_from_environment(self, mock_env_vars):
        """Test VISA_TYPE can be set via environment variable."""
        os.environ["VISA_TYPE"] = "work"
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.VISA_TYPE == "work"
    
    def test_default_embassy_location_is_kiew(self, mock_env_vars):
        """Test EMBASSY_LOCATION defaults to 'kiew'."""
        if "EMBASSY_LOCATION" in os.environ:
            del os.environ["EMBASSY_LOCATION"]
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.EMBASSY_LOCATION == "kiew"
    
    def test_embassy_location_from_environment(self, mock_env_vars):
        """Test EMBASSY_LOCATION can be set via environment variable."""
        os.environ["EMBASSY_LOCATION"] = "berlin"
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.EMBASSY_LOCATION == "berlin"
    
    def test_consulate_base_url_default(self, mock_env_vars):
        """Test default consulate URL."""
        if "CONSULATE_BASE_URL" in os.environ:
            del os.environ["CONSULATE_BASE_URL"]
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.CONSULATE_BASE_URL == "https://vis.diplo.de/rktermin/frontend/"


class TestLegacyConfiguration:
    """Test legacy configuration compatibility."""
    
    def test_category_id_default_is_schengen_kyiv(self, mock_env_vars):
        """Test default CATEGORY_ID matches Schengen in Kyiv."""
        if "CATEGORY_ID" in os.environ:
            del os.environ["CATEGORY_ID"]
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.CATEGORY_ID == "1497"  # Schengen Kyiv
    
    def test_category_id_custom_override(self, mock_env_vars):
        """Test CATEGORY_ID can be manually overridden."""
        os.environ["CATEGORY_ID"] = "1785"  # Work visa Kyiv
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.CATEGORY_ID == "1785"
    
    def test_realm_id_default(self, mock_env_vars):
        """Test default REALM_ID."""
        if "REALM_ID" in os.environ:
            del os.environ["REALM_ID"]
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.REALM_ID == "561"
    
    def test_location_code_matches_embassy_location(self, mock_env_vars):
        """Test LOCATION_CODE defaults to EMBASSY_LOCATION."""
        os.environ["EMBASSY_LOCATION"] = "berlin"
        if "LOCATION_CODE" in os.environ:
            del os.environ["LOCATION_CODE"]
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.LOCATION_CODE == "berlin"


class TestNotificationSettings:
    """Test notification and credentials configuration."""
    
    def test_telegram_bot_token_empty_by_default(self, mock_env_vars):
        """Test TELEGRAM_BOT_TOKEN is empty by default."""
        if "TELEGRAM_BOT_TOKEN" in os.environ:
            del os.environ["TELEGRAM_BOT_TOKEN"]
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.TELEGRAM_BOT_TOKEN == ""
    
    def test_telegram_credentials_from_environment(self, mock_env_vars):
        """Test Telegram credentials can be set via environment."""
        os.environ["TELEGRAM_BOT_TOKEN"] = "test_token_123"
        os.environ["TELEGRAM_CHAT_ID"] = "test_chat_456"
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.TELEGRAM_BOT_TOKEN == "test_token_123"
        assert config.TELEGRAM_CHAT_ID == "test_chat_456"
    
    def test_dbc_credentials_from_environment(self, mock_env_vars):
        """Test DeathByCaptcha credentials from environment."""
        os.environ["DBC_USERNAME"] = "test_user"
        os.environ["DBC_PASSWORD"] = "test_pass"
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.DBC_USERNAME == "test_user"
        assert config.DBC_PASSWORD == "test_pass"
    
    def test_dbc_binary_path_default(self, mock_env_vars):
        """Test default DeathByCaptcha binary path."""
        if "DBC_BINARY_PATH" in os.environ:
            del os.environ["DBC_BINARY_PATH"]
        
        if "lib.config" in sys.modules:
            del sys.modules["lib.config"]
        
        from lib import config
        assert config.DBC_BINARY_PATH == "lib/deathbycaptcha"


class TestDateFiltering:
    """Test date filtering logic."""
    
    def test_is_acceptable_date_function_exists(self):
        """Test that is_acceptable_date function exists."""
        from lib import config
        assert hasattr(config, "is_acceptable_date")
        assert callable(config.is_acceptable_date)
    
    def test_is_acceptable_date_returns_boolean(self):
        """Test that is_acceptable_date returns a boolean."""
        from lib import config
        result = config.is_acceptable_date(3, 25)
        assert isinstance(result, bool)
    
    def test_is_acceptable_date_march_after_24th(self):
        """Test example: March 25 is acceptable."""
        from lib import config
        # Config example: March after 24th is acceptable
        result = config.is_acceptable_date(3, 25)
        assert result is True
    
    def test_is_acceptable_date_april_before_24th(self):
        """Test example: April 23 is acceptable."""
        from lib import config
        # Config example: April before 24th is acceptable
        result = config.is_acceptable_date(4, 23)
        assert result is True
    
    def test_is_acceptable_date_outside_range(self):
        """Test dates outside acceptable range."""
        from lib import config
        # February should not be acceptable
        result = config.is_acceptable_date(2, 15)
        assert result is False


class TestHtmlSelectors:
    """Test HTML selector constants."""
    
    def test_html_selectors_defined(self):
        """Test that HTML selectors are defined."""
        from lib import config
        assert config.CAPTCHA_SELECTOR_MONTH == "appointment_captcha_month"
        assert config.REBOOK_CAPTCHA_SELECTOR == "rebook_captcha"
        assert config.CONTENT_DIV_ID == "content"
        assert config.ARROW_LINK_CLASS == "arrow"


class TestLoggingConfiguration:
    """Test logging configuration."""
    
    def test_logging_format_is_string(self):
        """Test logging format is defined."""
        from lib import config
        assert isinstance(config.LOGGING_FORMAT, str)
        assert "%(asctime)s" in config.LOGGING_FORMAT
        assert "%(levelname)s" in config.LOGGING_FORMAT
        assert "%(message)s" in config.LOGGING_FORMAT
    
    def test_logging_date_format_is_string(self):
        """Test logging date format is defined."""
        from lib import config
        assert isinstance(config.LOGGING_DATE_FORMAT, str)
        assert "%Y" in config.LOGGING_DATE_FORMAT
        assert "%m" in config.LOGGING_DATE_FORMAT
        assert "%d" in config.LOGGING_DATE_FORMAT
