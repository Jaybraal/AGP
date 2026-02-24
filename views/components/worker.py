"""QThread-based background worker for non-blocking DB/IO calls."""

from PyQt6.QtCore import QThread, pyqtSignal


class Worker(QThread):
    """
    Run any callable in a background thread.
    Connect .result(object) and .error(str) signals before calling .start().
    Keep a reference to the worker to prevent premature GC.
    """

    result = pyqtSignal(object)
    error  = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn     = fn
        self._args   = args
        self._kwargs = kwargs
        self.finished.connect(self.deleteLater)

    def run(self):
        try:
            r = self._fn(*self._args, **self._kwargs)
            self.result.emit(r)
        except Exception as exc:
            self.error.emit(str(exc))
