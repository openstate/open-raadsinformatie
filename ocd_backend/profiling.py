import StringIO
import cProfile
import os
import pstats
import time
from datetime import datetime
from functools import wraps

from celery import Celery as MainCelery

from ocd_backend.settings import ROOT_PATH


class Celery(MainCelery):
    def profile(self, run, min_seconds=1000):
        pr = cProfile.Profile()

        @wraps(run)
        def wrapper(*args, **kwargs):
            pr.enable()
            start_time = time.time()

            run_result = run(*args, **kwargs)

            end_time = time.time()
            pr.disable()

            time_delta = end_time - start_time
            if min_seconds and time_delta < min_seconds:
                return run_result

            s = StringIO.StringIO()
            ps = pstats.Stats(pr, stream=s)

            try:
                identifier = run_result.get_short_identifier()
            except:
                identifier = ''

            ps.dump_stats(os.path.join(
                ROOT_PATH,
                'celery_profiling_%s_%s_%s.prof' % (
                    datetime.utcnow().strftime('%m%d-%H%M'),
                    int(time_delta),
                    identifier
                )
            ))

            return run_result

        return wrapper
