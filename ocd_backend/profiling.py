import StringIO
import cProfile
import os
import pstats
from datetime import datetime
from functools import wraps

from celery import Celery as MainCelery

from ocd_backend.settings import ROOT_PATH


class Celery(MainCelery):
    def profile(self, run):
        pr = cProfile.Profile()

        @wraps(run)
        def wrapper(*args, **kwargs):
            pr.enable()
            run_result = run(*args, **kwargs)
            pr.disable()
            s = StringIO.StringIO()
            ps = pstats.Stats(pr, stream=s)
            ps.dump_stats(os.path.join(ROOT_PATH, 'celery_profiling_%s.prof' % datetime.utcnow().strftime('%Y%m%d%H%M%S')))

            return run_result
        return wrapper
