import warnings
from pathlib import Path
from xml.etree import ElementTree as ET

import structlog
from ofxtools.models.ofx import OFX
from ofxtools.Parser import OFXTree
from ofxtools.Types import OFXTypeError, OFXTypeWarning

logger = structlog.get_logger(__file__)
warnings.filterwarnings("ignore", category=OFXTypeWarning)


def parse_ofx(path: Path) -> OFX:
    """Parse an OFX file and return an OFX object."""

    ofx_tree = OFXTree()
    ofx_tree.parse(path)
    try:
        ofx: OFX = ofx_tree.convert()
    except OFXTypeError as e:
        logger.warning("Error parsing OFX file", error=str(e), name=path.name)
        # Attempt to fix the OFX file and try again
        fix_ofx(ofx_tree._root)
        ofx: OFX = ofx_tree.convert()
        logger.debug("Fixed OFX file", name=path.name)
    logger.debug("Parsed OFX file", name=path.name)
    return ofx


def fix_ofx(ofx_tree: ET.ElementTree) -> ET.ElementTree:
    """Attempt to fix an OFX file to be parsable by ofxtools."""

    # Change the severity to uppercase
    for element in ofx_tree.iter("SEVERITY"):
        element.text = element.text.upper()

    # For each STMTTRN tag, move the NAME tag to be the last child
    for element in ofx_tree.iter("STMTTRN"):
        name = element.find("NAME")
        element.remove(name)
        element.append(name)

    return ofx_tree
