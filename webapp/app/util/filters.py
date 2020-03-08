# Python standard library imports
from datetime import timedelta

# Local imports
#from ..app import app
#from saas.webapp import app
#from ..app import app as App
#from ..app import app
from saas.webapp.run import app

@app.template_filter()
def caps(text):
    """
    Convert a string to all caps.
    """
    return text.uppercase()

@app.template_filter("yes_no")
def yes_no(val):
    """
    Convert a boolean to Yes|No
    """
    return "Yes" if val else "No"


@app.template_filter("add_hours")
def add_hours(val, hours):
    """
    Convert a boolean to Yes|No
    """
    return val + timedelta(hours=hours)


#app.jinja_env.filters['yes_no'] = yes_no
