from dotty_dict import Dotty
from domain.exceptions import ImproperlyConfigured


class DottyConfDict(Dotty):

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise ImproperlyConfigured(
                f"The required configuration key '{key}' is missing"
            )
