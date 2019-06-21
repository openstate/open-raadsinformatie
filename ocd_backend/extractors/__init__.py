from datetime import datetime

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class BaseExtractor(object):
    """The base class that other extractors should inherit."""

    def __init__(self, source_definition):
        """
        :param source_definition: The configuration of a single source in
            the form of a dictionary (as defined in the settings).
        :type source_definition: dict.
        """
        self.source_definition = source_definition

    def run(self):
        """Starts the extraction process.

        This method must be implemented by the class that inherits the
        :py:class:`BaseExtractor` and should return a generator that
        yields one item per value. Items should be formatted as tuples
        containing the following elements (in this order):

        - the content-type of the data retrieved from the source (e.g.
          ``application/json``)
        - the data in it's original format, as retrieved from the source
          (as a string)
        """
        raise NotImplementedError

    def _interval_delta(self):
        """Returns a datetime delta.

        This method uses 'months_interval' specified in the source
        configuration, whichs defaults to 1 month. If the 'months_interval'
        is smaller than 2, the delta is split in two. Therefore, such
        intervals are measured in days instead of months.
        """
        months = 1  # Max 1 months intervals by default
        if 'months_interval' in self.source_definition:
            months = int(self.source_definition['months_interval'])

        if (months / 2.0) < 1.0:
            days = (months / 2.0) * 30
            return relativedelta(days=days)

        return relativedelta(months=months)

    def date_interval(self):
        """Returns a tuple of a start_date and end_date

        The interval are exactly the 'start_date' and 'end_date' specified
        in the source configuration. If one or both is not specified, the
        date will be the date of today with an offset calculated by
        :py:meth:`BaseExtractor._interval_delta`.

        :return: A start_date and end_date tuple
        :rtype: tuple
        """
        interval_delta = self._interval_delta()

        start_date = datetime.today() - interval_delta

        if 'start_date' in self.source_definition:
            start_date = parse(self.source_definition['start_date'])

        end_date = datetime.today() + interval_delta

        if 'end_date' in self.source_definition:
            end_date = parse(self.source_definition['end_date'])

        return start_date, end_date

    def interval_generator(self):
        """Returns a generator with date intervals

        The intervals are generated between the 'start_date' and 'end_date'
        specified in the source configuration. If one or both is not specified, the
        date will be the date of today with an offset calculated by
        :py:meth:`BaseExtractor._interval_delta`.

        :return: A generator yielding a start_date and end_date for each
        interval
        :rtype: generator
        """

        current_start, end_date = self.date_interval()

        while True:
            current_end = current_start + self._interval_delta()

            # If next current_end exceeds end_date then stop at end_date
            if current_end > end_date:
                current_end = end_date
                log.debug("Next interval exceeds %s, months_interval not used"
                          % end_date)

            yield current_start, current_end

            current_start = current_end + relativedelta(seconds=1)

            # Stop while loop if exceeded end_date
            if current_start > end_date:
                break
