"""tiny-decide: 5MB offline decision engine. Zero deps, <5ms CPU, no API key."""
from .decide import system_one, fit_temperatures
from .router import route
from .tokens import estimate_tokens
from .clean_email import clean_email_body

__version__ = "0.1.0"
__all__ = ["system_one", "fit_temperatures", "route", "estimate_tokens", "clean_email_body", "__version__"]
