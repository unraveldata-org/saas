# Python standard library imports
from datetime import datetime, timedelta

# Third-party imports

# Local imports


class Conversion(object):
    @classmethod
    def dt_to_unix_time_sec(cls, dt):
        """
        Convert the Datetime into epoch secs.
        :param dt: Python datetime object
        :return: Convert to epoch sec
        """
        epoch = datetime.utcfromtimestamp(0)
        return int((dt - epoch).total_seconds())

    @classmethod
    def dt_to_unix_time_ms(cls, dt):
        """
        Convert the Datetime into epoch milliseconds.
        :param dt: Python datetime object
        :return: Convert to epoch ms
        """
        epoch = datetime.utcfromtimestamp(0)
        return int((dt - epoch).total_seconds() * 1000)

    @classmethod
    def unix_time_ms_to_dt(cls, epoch_ms):
        """
        Convert epoch ms to a Python DateTime object in UTC.
        :param epoch_ms: Epoch time in ms (int)
        :return: Return a Python DateTime object in UTC.
        """
        return datetime.utcfromtimestamp(epoch_ms / 1000)

    @classmethod
    def unix_time_sec_to_dt(cls, epoch_sec):
        """
        Convert epoch sec to a Python DateTime object in UTC.
        :param epoch_sec: Epoch time in sec (int)
        :return: Return a Python DateTime object in UTC.
        """
        return datetime.utcfromtimestamp(epoch_sec)
