"""
Nilvera Python Client
~~~~~~~~~~~~~~~~~~~~~

Nilvera E-Fatura ve E-Arşiv REST API için Python client kütüphanesi.

Temel Kullanım:

    >>> from nilvera_client import NilveraClient
    >>> client = NilveraClient(api_key='your-api-key', environment='test')
    >>> result = client.test_connection()
    >>> print(result)

:copyright: (c) 2026
:license: MIT, see LICENSE for more details.
"""

__version__ = '1.1.0'
__author__ = 'Abdullah'
__license__ = 'MIT'

from .client import NilveraClient
from .currency import TCMBCurrencyService
from .exceptions import (
    NilveraException,
    NilveraConnectionError,
    NilveraTimeoutError,
    NilveraAPIError
)

__all__ = [
    'NilveraClient',
    'TCMBCurrencyService',
    'NilveraException',
    'NilveraConnectionError',
    'NilveraTimeoutError',
    'NilveraAPIError',
]
