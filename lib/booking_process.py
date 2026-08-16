"""
Booking process adapter for German visa appointments.
Auto-detects and adapts to different embassy portal layouts and booking processes.
Supports both legacy and new German embassy appointment systems.
"""
from typing import Optional, Dict, List, Any, TYPE_CHECKING

from . import utils, config

if TYPE_CHECKING:
    from bs4 import BeautifulSoup


class BookingProcessDetector:
    """Detects the type of booking portal and adapts extraction logic accordingly"""
    
    # Portal signatures for identification
    PORTAL_SIGNATURES = {
        "legacy_rktermin": {
            "indicators": ["rktermin", "frontend", "appointment_captcha"],
            "description": "Legacy RKTerMin portal (before 2024)",
        },
        "new_termin": {
            "indicators": ["termin", "digital", "appointment_form", "new_booking"],
            "description": "New digital portal (2024+)",
        },
        "doctolib": {
            "indicators": ["doctolib", "doctorlib", "appointment_system"],
            "description": "Doctolib-based system (some embassies)",
        },
        "custom_embassy": {
            "indicators": ["embassy", "consulate", "appointment", "available"],
            "description": "Custom embassy system",
        },
    }
    
    def __init__(self):
        self.logger = utils.setup_logger()
        self.detected_portal = None
        self.portal_metadata = {}
    
    def detect_portal_type(self, html_content: Any) -> str:
        """
        Detect the type of booking portal from HTML content.
        
        Args:
            html_content: Any HTML object
            
        Returns:
            Portal type identifier or 'unknown'
        """
        html_text = str(html_content).lower()
        
        for portal_type, signature in self.PORTAL_SIGNATURES.items():
            if all(indicator in html_text for indicator in signature["indicators"]):
                self.detected_portal = portal_type
                self.logger.info(f"Detected portal type: {portal_type}")
                return portal_type
        
        self.logger.warning("Unknown portal type detected")
        return "unknown"
    
    def get_portal_description(self) -> Optional[str]:
        """Get human-readable description of detected portal"""
        if not self.detected_portal or self.detected_portal == "unknown":
            return None
        
        return self.PORTAL_SIGNATURES.get(self.detected_portal, {}).get("description")
    
    def extract_form_fields(self, html_content: Any) -> Dict[str, List[str]]:
        """
        Extract all form fields from the HTML to understand required information.
        
        Args:
            html_content: Any HTML object
            
        Returns:
            Dictionary of form fields found: {field_type: [field_names]}
        """
        fields = {
            "text_inputs": [],
            "selects": [],
            "checkboxes": [],
            "radios": [],
            "textareas": [],
            "hidden": [],
        }
        
        try:
            # Find all form elements
            forms = html_content.find_all("form")
            for form in forms:
                # Text inputs
                for inp in form.find_all("input", {"type": ["text", "email", "date", "number"]}):
                    name = inp.get("name", inp.get("id", "unknown"))
                    fields["text_inputs"].append(name)
                
                # Selects
                for sel in form.find_all("select"):
                    name = sel.get("name", sel.get("id", "unknown"))
                    fields["selects"].append(name)
                
                # Checkboxes
                for chk in form.find_all("input", {"type": "checkbox"}):
                    name = chk.get("name", chk.get("id", "unknown"))
                    fields["checkboxes"].append(name)
                
                # Radio buttons
                for rad in form.find_all("input", {"type": "radio"}):
                    name = rad.get("name", rad.get("id", "unknown"))
                    fields["radios"].append(name)
                
                # Textareas
                for txt in form.find_all("textarea"):
                    name = txt.get("name", txt.get("id", "unknown"))
                    fields["textareas"].append(name)
                
                # Hidden fields
                for hid in form.find_all("input", {"type": "hidden"}):
                    name = hid.get("name", hid.get("id", "unknown"))
                    fields["hidden"].append(name)
            
            self.logger.debug(f"Extracted form fields: {fields}")
            return fields
            
        except Exception as e:
            self.logger.error(f"Error extracting form fields: {e}")
            return fields
    
    def detect_appointment_slots(self, html_content: Any) -> List[str]:
        """
        Detect available appointment slots/dates from page.
        Adapts to different portal layouts.
        
        Args:
            html_content: Any HTML object
            
        Returns:
            List of detected appointment dates/slots
        """
        slots = []
        
        try:
            # Try multiple selectors for different portal types
            selectors = [
                # Legacy RKTerMin
                {"class": "appointment"},
                {"id": "available-dates"},
                {"class": "slot"},
                {"class": "date-slot"},
                # New systems
                {"class": "available"},
                {"class": "slot-available"},
                {"data-available": True},
                # Generic date elements
                {"datetime": True},
            ]
            
            for selector in selectors:
                elements = html_content.find_all(attrs=selector)
                for elem in elements:
                    date_str = elem.get_text(strip=True)
                    if date_str and len(date_str) > 0:
                        slots.append(date_str)
            
            if slots:
                self.logger.info(f"Detected {len(slots)} available slots")
            else:
                self.logger.debug("No appointment slots detected")
            
            return list(set(slots))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error detecting appointment slots: {e}")
            return []
    
    def detect_captcha_type(self, html_content: Any) -> Optional[str]:
        """
        Detect what type of captcha is used on the page.
        
        Args:
            html_content: Any HTML object
            
        Returns:
            Captcha type identifier or None
        """
        html_text = str(html_content).lower()
        
        if "recaptcha" in html_text:
            self.logger.info("Detected reCAPTCHA")
            return "recaptcha"
        elif "hcaptcha" in html_text:
            self.logger.info("Detected hCaptcha")
            return "hcaptcha"
        elif "appointment_captcha" in html_text:
            self.logger.info("Detected custom appointment captcha")
            return "appointment_captcha"
        else:
            self.logger.warning("Could not detect captcha type")
            return None


class PortalLayoutAdapter:
    """Adapts extraction and booking logic to different portal layouts"""
    
    def __init__(self, portal_type: str):
        self.logger = utils.setup_logger()
        self.portal_type = portal_type
    
    def extract_available_dates(
        self, 
        html_content: Any, 
        config_obj: Any
    ) -> Optional[str]:
        """
        Extract available dates using portal-specific logic.
        
        Args:
            html_content: Any HTML object
            config_obj: Configuration object with date filtering
            
        Returns:
            Available date string or None
        """
        if self.portal_type == "legacy_rktermin":
            return self._extract_legacy_rktermin_dates(html_content, config_obj)
        elif self.portal_type == "new_termin":
            return self._extract_new_termin_dates(html_content, config_obj)
        elif self.portal_type == "doctolib":
            return self._extract_doctolib_dates(html_content, config_obj)
        else:
            return self._extract_generic_dates(html_content, config_obj)
    
    def _extract_legacy_rktermin_dates(
        self, 
        html_content: Any, 
        config_obj: Any
    ) -> Optional[str]:
        """Extract dates from legacy RKTerMin system"""
        try:
            content_div = html_content.find("div", {"id": "content"})
            if not content_div:
                self.logger.error("Content div not found")
                return None
            
            h4_elements = content_div.find_all("h4")
            
            for elem in h4_elements:
                text = elem.text.strip()
                tokens = text.split(" ")
                
                if len(tokens) < 2:
                    continue
                
                date_tokens = tokens[1].split(".")
                
                if len(date_tokens) != 3:
                    continue
                
                try:
                    day = int(date_tokens[0])
                    month = int(date_tokens[1])
                    
                    if config_obj.is_acceptable_date(month, day):
                        available_date = '.'.join(date_tokens)
                        self.logger.info(f"Found acceptable date (legacy): {available_date}")
                        return available_date
                        
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting legacy dates: {e}")
            return None
    
    def _extract_new_termin_dates(
        self, 
        html_content: Any, 
        config_obj: Any
    ) -> Optional[str]:
        """Extract dates from new digital portal system"""
        try:
            # New systems often use data attributes or specific classes
            date_elements = html_content.find_all(
                attrs={"class": ["appointment-date", "slot-date", "available-date"]}
            )
            
            for elem in date_elements:
                # Try multiple ways to get the date
                date_str = (
                    elem.get("data-date") or 
                    elem.get_text(strip=True) or 
                    elem.get("title", "")
                )
                
                if not date_str:
                    continue
                
                # Parse date (format may vary)
                parts = date_str.replace("-", ".").replace("/", ".").split(".")
                
                if len(parts) >= 2:
                    try:
                        day = int(parts[0]) if len(parts[0]) <= 2 else int(parts[1])
                        month = int(parts[1]) if len(parts[1]) <= 2 else int(parts[0])
                        
                        if config_obj.is_acceptable_date(month, day):
                            # Reconstruct date in DD.MM.YYYY format
                            year = parts[2] if len(parts) > 2 else "2024"
                            available_date = f"{day:02d}.{month:02d}.{year}"
                            self.logger.info(f"Found acceptable date (new): {available_date}")
                            return available_date
                    except (ValueError, IndexError):
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting new portal dates: {e}")
            return None
    
    def _extract_doctolib_dates(
        self, 
        html_content: Any, 
        config_obj: Any
    ) -> Optional[str]:
        """Extract dates from Doctolib-based system"""
        try:
            # Doctolib uses specific structure for appointments
            appointment_slots = html_content.find_all(
                attrs={"class": ["appointment-slot", "slot", "doctolib-slot"]}
            )
            
            for slot in appointment_slots:
                date_elem = slot.find(attrs={"class": ["slot-date", "date"]})
                if date_elem:
                    date_str = date_elem.get_text(strip=True)
                    
                    # Doctolib typically uses DD.MM.YYYY or similar
                    parts = date_str.replace("-", ".").replace("/", ".").split(".")
                    
                    if len(parts) >= 2:
                        try:
                            day = int(parts[0])
                            month = int(parts[1])
                            
                            if config_obj.is_acceptable_date(month, day):
                                year = parts[2] if len(parts) > 2 else "2024"
                                available_date = f"{day:02d}.{month:02d}.{year}"
                                self.logger.info(f"Found acceptable date (Doctolib): {available_date}")
                                return available_date
                        except (ValueError, IndexError):
                            continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting Doctolib dates: {e}")
            return None
    
    def _extract_generic_dates(
        self, 
        html_content: Any, 
        config_obj: Any
    ) -> Optional[str]:
        """Generic date extraction for unknown portal types"""
        try:
            # Try to find any element with date-like content
            for elem in html_content.find_all(["div", "span", "td", "li"]):
                text = elem.get_text(strip=True)
                
                # Check if it looks like a date
                if any(sep in text for sep in [".", "-", "/"]):
                    parts = text.replace("-", ".").replace("/", ".").split(".")
                    
                    if len(parts) >= 2:
                        try:
                            # Try different orderings
                            for day, month in [(0, 1), (1, 0)]:
                                try:
                                    d = int(parts[day])
                                    m = int(parts[month])
                                    
                                    if 1 <= d <= 31 and 1 <= m <= 12:
                                        if config_obj.is_acceptable_date(m, d):
                                            year = parts[2] if len(parts) > 2 else "2024"
                                            available_date = f"{d:02d}.{m:02d}.{year}"
                                            self.logger.info(f"Found acceptable date (generic): {available_date}")
                                            return available_date
                                except (ValueError, IndexError):
                                    continue
                        except ValueError:
                            continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in generic date extraction: {e}")
            return None
