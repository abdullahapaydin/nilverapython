# nilvera_client/currency.py
# TCMB (Türkiye Cumhuriyet Merkez Bankası) Döviz Kuru Servisi

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TCMBCurrencyService:
    """TCMB'den döviz kurlarını çeker"""
    
    BASE_URL = "https://www.tcmb.gov.tr/kurlar"
    
    @staticmethod
    def get_exchange_rate(currency_code: str = "USD", date: datetime = None, rate_type: str = "ForexBuying"):
        """
        TCMB'den döviz kuru çeker
        
        Args:
            currency_code: Para birimi kodu (USD, EUR, GBP, vb.)
            date: Kur tarihi (None ise bugün)
            rate_type: Kur tipi
                - ForexBuying: Döviz Alış (Efektif Alış)
                - ForexSelling: Döviz Satış (Efektif Satış)
                - BanknoteBuying: Banknot Alış
                - BanknoteSelling: Banknot Satış
        
        Returns:
            dict: {
                'success': bool,
                'rate': float or None,
                'date': str (YYYY-MM-DD),
                'currency': str,
                'rate_type': str,
                'error': str (hata durumunda)
            }
        """
        if date is None:
            date = datetime.now()
        
        # Hafta sonu kontrolü - geriye doğru iş günü ara
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            # Cumartesi (5) veya Pazar (6) ise bir gün geriye git
            if date.weekday() >= 5:
                date = date - timedelta(days=1)
                attempt += 1
                continue
            
            # Kur verilerini çekmeyi dene
            result = TCMBCurrencyService._fetch_rate_for_date(currency_code, date, rate_type)
            
            if result['success']:
                return result
            
            # Başarısızsa (tatil günü olabilir) bir gün geriye git
            logger.debug(f"Kur bulunamadı ({date.strftime('%Y-%m-%d')}), önceki güne bakılıyor...")
            date = date - timedelta(days=1)
            attempt += 1
        
        return {
            'success': False,
            'rate': None,
            'date': None,
            'currency': currency_code,
            'rate_type': rate_type,
            'error': f'Son {max_attempts} gün içinde kur bulunamadı'
        }
    
    @staticmethod
    def _fetch_rate_for_date(currency_code: str, date: datetime, rate_type: str):
        """Belirli bir tarih için kur çeker"""
        try:
            # TCMB URL formatı: https://www.tcmb.gov.tr/kurlar/YYYYMM/DDMMYYYY.xml
            date_str = date.strftime("%d%m%Y")
            month_str = date.strftime("%Y%m")
            url = f"{TCMBCurrencyService.BASE_URL}/{month_str}/{date_str}.xml"
            
            logger.debug(f"TCMB URL: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'rate': None,
                    'date': date.strftime('%Y-%m-%d'),
                    'currency': currency_code,
                    'rate_type': rate_type,
                    'error': f'TCMB yanıt vermedi: HTTP {response.status_code}'
                }
            
            # XML parse et
            root = ET.fromstring(response.content)
            
            # Para birimini bul
            for currency in root.findall('Currency'):
                code = currency.get('CurrencyCode') or currency.get('Kod')
                
                if code == currency_code:
                    # Kur tipine göre değeri al
                    rate_element = currency.find(rate_type)
                    
                    if rate_element is not None and rate_element.text:
                        rate_value = float(rate_element.text.replace(',', '.'))
                        
                        logger.debug(f"TCMB Kur bulundu: {currency_code} = {rate_value} TRY ({date.strftime('%Y-%m-%d')})")
                        
                        return {
                            'success': True,
                            'rate': rate_value,
                            'date': date.strftime('%Y-%m-%d'),
                            'currency': currency_code,
                            'rate_type': rate_type,
                            'source': 'TCMB'
                        }
            
            return {
                'success': False,
                'rate': None,
                'date': date.strftime('%Y-%m-%d'),
                'currency': currency_code,
                'rate_type': rate_type,
                'error': f'{currency_code} bulunamadı'
            }
        
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'rate': None,
                'date': date.strftime('%Y-%m-%d'),
                'currency': currency_code,
                'rate_type': rate_type,
                'error': 'TCMB bağlantı zaman aşımı'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'rate': None,
                'date': date.strftime('%Y-%m-%d'),
                'currency': currency_code,
                'rate_type': rate_type,
                'error': f'Bağlantı hatası: {str(e)}'
            }
        except ET.ParseError as e:
            return {
                'success': False,
                'rate': None,
                'date': date.strftime('%Y-%m-%d'),
                'currency': currency_code,
                'rate_type': rate_type,
                'error': f'XML parse hatası: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'rate': None,
                'date': date.strftime('%Y-%m-%d'),
                'currency': currency_code,
                'rate_type': rate_type,
                'error': f'Beklenmeyen hata: {str(e)}'
            }
    
    @staticmethod
    def get_latest_usd_buy_rate():
        """USD Alış kurunu çeker (bugün veya en yakın iş günü)"""
        return TCMBCurrencyService.get_exchange_rate('USD', rate_type='ForexBuying')
    
    @staticmethod
    def get_latest_eur_buy_rate():
        """EUR Alış kurunu çeker (bugün veya en yakın iş günü)"""
        return TCMBCurrencyService.get_exchange_rate('EUR', rate_type='ForexBuying')
