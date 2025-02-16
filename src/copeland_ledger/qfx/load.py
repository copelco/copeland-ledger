from pathlib import Path

from .extract import parse_ofx
from ..models import Statement, StatementList
from .transform import transform_ofx

import structlog

logger = structlog.getLogger(__name__)


def load(path: str) -> StatementList:
    ofx_path = Path(path)
    logger.debug("Loading OFX file", name=ofx_path.name)
    ofx = parse_ofx(path=ofx_path)
    return transform_ofx(ofx=ofx)


def load_statement(path: str, acctid_suffix: str) -> Statement | None:
    statement_list = load(path=path)
    return statement_list.get_by_acctid_suffix(suffix=acctid_suffix)
