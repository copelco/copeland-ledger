import re
import warnings
from pathlib import Path
from xml.etree import ElementTree as ET

import structlog
from ofxtools.models.base import Aggregate
from ofxtools.Parser import OFXTree
from ofxtools.Types import OFXTypeError, OFXTypeWarning

logger = structlog.get_logger(__file__)
warnings.filterwarnings("ignore", category=OFXTypeWarning)


ACCOUNT_ID_RE = re.compile(r"ACCTID>(?P<account_id>[\w\-|]+)")


def ofx_content_contains_account_id_suffix(ofx_content: str, account_id_suffix: str) -> bool:
    """Quickly inspect OFX file contents for the given account ID."""
    if match_result := ACCOUNT_ID_RE.search(ofx_content):
        ofx_account_id = match_result.group("account_id")
        if ofx_account_id.endswith(account_id_suffix):
            logger.debug(
                "Found account ID suffix in OFX content",
                acct_id_suffix=account_id_suffix,
            )
            return True
    return False


def parse_ofx(path: Path) -> Aggregate:
    """Parse an OFX file and return an OFX object."""

    ofx_tree = OFXTree()
    ofx_tree.parse(path)
    try:
        ofx = ofx_tree.convert()
    except OFXTypeError as e:
        logger.warning("Error parsing OFX file", error=str(e), name=path.name)
        # Attempt to fix the OFX file and try again
        fix_ofx(root_element=ofx_tree._root)
        ofx = ofx_tree.convert()
        logger.debug("Fixed OFX file", name=path.name)
    logger.debug("Parsed OFX file", name=path.name)
    return ofx


def fix_ofx(root_element: ET.Element) -> ET.Element:
    """Attempt to fix an OFX file to be parsable by ofxtools."""

    # Change the severity to uppercase
    for element in root_element.iter("SEVERITY"):
        if element.text is not None:
            element.text = element.text.upper()

    # For each STMTTRN tag, move the NAME tag to be the last child
    for element in root_element.iter("STMTTRN"):
        name = element.find("NAME")
        if name is not None:
            element.remove(name)
            element.append(name)

    return root_element
