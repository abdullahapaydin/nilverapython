"""
Nilvera Client Exception Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bu modül Nilvera client için exception sınıflarını tanımlar.
"""


class NilveraException(Exception):
    """Tüm Nilvera exception'larının temel sınıfı"""
    pass


class NilveraConnectionError(NilveraException):
    """Nilvera API'ye bağlanırken oluşan hatalar"""
    pass


class NilveraTimeoutError(NilveraException):
    """Nilvera API istekleri zaman aşımına uğradığında"""
    pass


class NilveraAPIError(NilveraException):
    """Nilvera API'den dönen HTTP hataları"""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
