from datetime import datetime
from ocd_backend.log import get_source_logger
from ocd_backend.settings import DATA_DIR_PATH

log = get_source_logger('finalizer')

class IndexedFile():
    def __init__(self, filename):
        if filename is not None:
            self.filename = f"{DATA_DIR_PATH}/{filename}"
        else:
            self.filename = None

    def signal_start(self, source):
        if self.filename is None:
            return

        try:
            with open(self.filename, "a+") as f:
                f.write(f"{source},START,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            log.warning(f"[{source}] error occurred when signalling start to indexed file: {e}")

    def signal_end(self, source):
        if self.filename is None:
            return

        try:
            with open(self.filename, "a+") as f:
                f.write(f"{source},END,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            log.warning(f"[{source}] error occurred when signalling end to indexed file: {e}")
