"""
Nilvera Python Client - Basit Testler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Temel fonksiyonların çalışıp çalışmadığını test eder.
"""

import unittest
from unittest.mock import Mock, patch
from nilvera_client import NilveraClient, TCMBCurrencyService
from nilvera_client.exceptions import (
    NilveraException,
    NilveraConnectionError,
    NilveraTimeoutError,
    NilveraAPIError
)


class TestNilveraClient(unittest.TestCase):
    """NilveraClient temel testleri"""
    
    def setUp(self):
        """Her test öncesi çalışır"""
        self.api_key = "test-api-key-123"
        self.client = NilveraClient(api_key=self.api_key, environment='test')
    
    def test_init_test_environment(self):
        """Test ortamı başlatma testi"""
        client = NilveraClient(api_key="test-key", environment='test')
        self.assertEqual(client.base_url, "https://apitest.nilvera.com")
        self.assertEqual(client.environment, "test")
    
    def test_init_production_environment(self):
        """Production ortamı başlatma testi"""
        client = NilveraClient(api_key="prod-key", environment='production')
        self.assertEqual(client.base_url, "https://api.nilvera.com")
        self.assertEqual(client.environment, "production")
    
    def test_custom_url(self):
        """Özel URL testi"""
        custom_url = "https://custom-api.example.com"
        client = NilveraClient(
            api_key="test-key",
            environment='test',
            test_url=custom_url
        )
        self.assertEqual(client.base_url, custom_url)
    
    def test_session_headers(self):
        """Session header'larının doğru ayarlanması testi"""
        self.assertEqual(
            self.client.session.headers['Authorization'],
            f'Bearer {self.api_key}'
        )
        self.assertEqual(
            self.client.session.headers['Content-Type'],
            'application/json-patch+json'
        )


class TestTCMBCurrencyService(unittest.TestCase):
    """TCMB Currency Service testleri"""
    
    @patch('nilvera_client.currency.requests.get')
    def test_successful_currency_fetch(self, mock_get):
        """Başarılı kur çekme testi"""
        # Mock XML response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''<?xml version="1.0" encoding="UTF-8"?>
        <Tarih_Date Tarih="15.02.2026" Date="02/15/2026">
            <Currency CurrencyCode="USD">
                <ForexBuying>34.5678</ForexBuying>
            </Currency>
        </Tarih_Date>'''
        mock_get.return_value = mock_response
        
        result = TCMBCurrencyService.get_exchange_rate('USD')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['rate'], 34.5678)
        self.assertEqual(result['currency'], 'USD')
    
    def test_currency_service_methods(self):
        """Currency service metodlarının varlığı testi"""
        self.assertTrue(hasattr(TCMBCurrencyService, 'get_exchange_rate'))
        self.assertTrue(hasattr(TCMBCurrencyService, 'get_latest_usd_buy_rate'))
        self.assertTrue(hasattr(TCMBCurrencyService, 'get_latest_eur_buy_rate'))


class TestExceptions(unittest.TestCase):
    """Exception sınıfları testleri"""
    
    def test_nilvera_exception(self):
        """NilveraException testi"""
        exc = NilveraException("Test error")
        self.assertIsInstance(exc, Exception)
        self.assertEqual(str(exc), "Test error")
    
    def test_nilvera_connection_error(self):
        """NilveraConnectionError testi"""
        exc = NilveraConnectionError("Connection failed")
        self.assertIsInstance(exc, NilveraException)
        self.assertEqual(str(exc), "Connection failed")
    
    def test_nilvera_timeout_error(self):
        """NilveraTimeoutError testi"""
        exc = NilveraTimeoutError("Timeout")
        self.assertIsInstance(exc, NilveraException)
    
    def test_nilvera_api_error(self):
        """NilveraAPIError testi"""
        exc = NilveraAPIError("API Error", status_code=400, response="Bad Request")
        self.assertIsInstance(exc, NilveraException)
        self.assertEqual(exc.status_code, 400)
        self.assertEqual(exc.response, "Bad Request")


class TestClientMethods(unittest.TestCase):
    """Client metodları varlık testleri"""
    
    def setUp(self):
        self.client = NilveraClient(api_key="test-key", environment='test')
    
    def test_has_test_connection_method(self):
        """test_connection metodu varlık testi"""
        self.assertTrue(hasattr(self.client, 'test_connection'))
        self.assertTrue(callable(self.client.test_connection))
    
    def test_has_invoice_methods(self):
        """Fatura metodları varlık testleri"""
        methods = [
            'get_einvoice_series',
            'get_series_detail',
            'create_draft_invoice',
            'confirm_and_send_draft',
            'get_invoice_status',
            'check_from_gtb',
            'get_invoice_details',
            'get_invoice_pdf',
            'get_invoice_html',
            'get_invoice_xml',
            'cancel_draft_invoice',
        ]
        
        for method in methods:
            self.assertTrue(hasattr(self.client, method), f"Missing method: {method}")
            self.assertTrue(callable(getattr(self.client, method)))
    
    def test_has_incoming_invoice_methods(self):
        """Gelen fatura metodları varlık testleri"""
        methods = [
            'get_incoming_invoices',
            'get_incoming_invoice_details',
        ]
        
        for method in methods:
            self.assertTrue(hasattr(self.client, method), f"Missing method: {method}")


def run_tests():
    """Testleri çalıştır"""
    # Test suite oluştur
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Tüm test sınıflarını ekle
    suite.addTests(loader.loadTestsFromTestCase(TestNilveraClient))
    suite.addTests(loader.loadTestsFromTestCase(TestTCMBCurrencyService))
    suite.addTests(loader.loadTestsFromTestCase(TestExceptions))
    suite.addTests(loader.loadTestsFromTestCase(TestClientMethods))
    
    # Testleri çalıştır
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Sonuçları yazdır
    print("\\n" + "=" * 60)
    print(f"Testler tamamlandı!")
    print(f"  Toplam: {result.testsRun}")
    print(f"  ✅ Başarılı: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  ❌ Başarısız: {len(result.failures)}")
    print(f"  🔥 Hata: {len(result.errors)}")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
