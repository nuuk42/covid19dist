# service utilities
import logging
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
def get_numeric_loglevel(loglevel_string):
    return {'NOTSET':0,'DEBUG':10,'INFO':20,'WARNING':30,'ERROR':40,'CRITICAL':50}[loglevel_string]

