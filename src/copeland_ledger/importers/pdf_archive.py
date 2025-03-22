import re
from pathlib import Path

import beangulp
import structlog
from beangulp import mimetypes
from pypdf import PdfReader


logger = structlog.get_logger(__file__)

VALID_MIMETYPES = {"application/pdf"}


def find_account_id_suffix_in_pdf(acctid_suffix: str, content: str) -> bool:
    """Search for an account ID suffix in the given content."""
    if m := re.search(rf"\s*({acctid_suffix})\s*", content):
        return acctid_suffix == m.group(1)
    return False


def find_org_name_in_pdf(org: str, content: str) -> bool:
    """Search for the organization name in the given content."""
    if m := re.search(rf"\s*({org})\s*", content):
        return org == m.group(1)
    return False


def extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(path)
    content = ""
    for page in reader.pages:
        content += page.extract_text()
    return content


class PdfArchiver(beangulp.Importer):
    """A beangulp importer to archive PDF files (no transactions are extracted)."""

    def __init__(self, org: str, acctid_suffix: str, bean_account: str):
        self.bean_account = bean_account
        self.org = org
        self.acctid_suffix = acctid_suffix
        logger.debug(
            "Initialized PdfArchiver",
            bean_account=bean_account,
            org=org,
            acctid_suffix=acctid_suffix,
        )

    def account(self, filepath):
        """Return the account to archive the file to."""
        return self.bean_account

    def filename(self, filepath: str) -> str:
        """Return the archival filename for the given file."""
        path = Path(filepath)
        return f"{self.org}_{self.acctid_suffix}-statement{path.suffix}"

    def identify(self, filepath: str) -> bool:
        """Return True if this importer matches a PDF file."""

        path = Path(filepath)
        if path.suffix != ".pdf":
            return False

        # Match for a compatible MIME type.
        mimetype, _ = mimetypes.guess_type(filepath, strict=False)
        if mimetype not in VALID_MIMETYPES:
            return False

        content = extract_pdf_text(path=path)

        if find_account_id_suffix_in_pdf(
            acctid_suffix=self.acctid_suffix, content=content
        ) and find_org_name_in_pdf(org=self.org, content=content):
            logger.info(
                "Identified PDF file",
                filename=path.name,
                acctid_suffix=self.acctid_suffix,
                ofx_org=self.org,
            )
            return True

        return False
