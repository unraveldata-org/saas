# Python Standard Library imports
import logging
from collections import defaultdict

class Utils:
    @staticmethod
    def get_logger(name):
        """
        Get a default logger
        :param name: Logger name
        :return: Return the logger object
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        logger.addHandler(ch)

        return logger

    @staticmethod
    def safe_get(root_dict, list_keys, default_value=None):
        """
        Helper method to safely get a sequence of keys from a dictionary.
        If for whatever reason the dictionary is None, input list of keys is invalid, or a key is not found,
        then return the default_value. If all keys are present, then return the ultimate value.
        :param root_dict: Dictionary or defaultdict object
        :param list_keys: List of keys, each of which can be of any type
        :param default_value: Default value to return
        :return: Return the value that corresponds to the list of keys if all present, otherwise, return the default_value.
        """
        if root_dict is None:
            return default_value

        if list_keys is None or len(list_keys) == 0:
            return default_value

        dict_types = [dict, defaultdict]

        curr_obj = root_dict
        for k in list_keys:
            if type(curr_obj) in dict_types and k in curr_obj:
                curr_obj = curr_obj[k]
            else:
                curr_obj = default_value
                break

        return curr_obj
