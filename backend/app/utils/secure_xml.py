"""
Secure XML Parser Utility
Provides secure XML parsing methods that prevent XXE attacks
"""

import defusedxml.ElementTree as ET
from defusedxml import DefusedXmlException
import xml.etree.ElementTree as UnsafeET
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)


def parse_xml_string(xml_content: str, use_defused: bool = True) -> Optional[ET.Element]:
    """
    Safely parse XML string content

    Args:
        xml_content: XML content as string
        use_defused: Use defused XML parser (recommended for security)

    Returns:
        Parsed XML root element or None on error
    """
    if not xml_content:
        return None

    try:
        if use_defused:
            # Use defused XML to prevent XXE attacks
            return ET.fromstring(xml_content)
        else:
            # Fallback to standard parser with security restrictions
            parser = UnsafeET.XMLParser(
                resolve_entities=False,  # Disable entity resolution
                forbid_dtd=True,         # Forbid DTD processing
                forbid_entities=True,    # Forbid entities
                forbid_external=True     # Forbid external references
            )
            return UnsafeET.fromstring(xml_content, parser=parser)
    except DefusedXmlException as e:
        logger.error(f"Potentially malicious XML detected: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        return None


def parse_xml_file(file_path: str, use_defused: bool = True) -> Optional[ET.Element]:
    """
    Safely parse XML file

    Args:
        file_path: Path to XML file
        use_defused: Use defused XML parser (recommended for security)

    Returns:
        Parsed XML root element or None on error
    """
    try:
        if use_defused:
            # Use defused XML to prevent XXE attacks
            tree = ET.parse(file_path)
            return tree.getroot()
        else:
            # Fallback to standard parser with security restrictions
            parser = UnsafeET.XMLParser(
                resolve_entities=False,
                forbid_dtd=True,
                forbid_entities=True,
                forbid_external=True
            )
            tree = UnsafeET.parse(file_path, parser=parser)
            return tree.getroot()
    except DefusedXmlException as e:
        logger.error(f"Potentially malicious XML file detected: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing XML file: {e}")
        return None


def validate_xml_size(xml_content: Union[str, bytes], max_size_mb: int = 10) -> bool:
    """
    Validate XML content size to prevent DoS attacks

    Args:
        xml_content: XML content to validate
        max_size_mb: Maximum allowed size in megabytes

    Returns:
        True if size is within limits, False otherwise
    """
    if isinstance(xml_content, str):
        size = len(xml_content.encode('utf-8'))
    else:
        size = len(xml_content)

    max_bytes = max_size_mb * 1024 * 1024

    if size > max_bytes:
        logger.warning(f"XML content exceeds size limit: {size} bytes > {max_bytes} bytes")
        return False

    return True