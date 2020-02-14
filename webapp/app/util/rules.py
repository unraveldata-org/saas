# Python standard library imports

# Third-party imports
# https://pypi.org/project/flask-request-validator/
from flask_request_validator import AbstractRule

# Third Party imports (sorted alphabetically)
# https://pypi.org/project/email-validator/
from email_validator import validate_email, EmailNotValidError

# Local imports


class RuleEmail(AbstractRule):
    """
    Flask Request Validator that ensures an email is properly constructed.
    """

    def validate(self, value):
        """
        Validate the email. Return a list of error messages.
        :param value: Email value (str)
        :return: Return a list of human-readable errors found.
        """
        errors = []

        try:
            v = validate_email(value)  # validate and get info
            email = v["email"]  # replace with normalized form
        except EmailNotValidError as e:
            # email is not valid, exception message is human-readable
            errors.append(str(e))

        return errors
