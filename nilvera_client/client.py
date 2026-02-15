# nilvera_client/client.py
# Nilvera REST API Client - İhracat E-Fatura Entegrasyonu

import requests
import json
import uuid
import logging
from datetime import datetime
from .exceptions import NilveraConnectionError, NilveraTimeoutError, NilveraAPIError

logger = logging.getLogger(__name__)


class NilveraClient:
    """Nilvera REST API istemcisi - İhracat E-Fatura operasyonları"""

    BASE_URLS = {
        'test': 'https://apitest.nilvera.com',
        'production': 'https://api.nilvera.com'
    }

    def __init__(self, api_key: str, environment: str = 'test', 
                 test_url: str = None, production_url: str = None):
        """
        Nilvera Client başlatır
        
        Args:
            api_key: Nilvera API anahtarı
            environment: 'test' veya 'production'
            test_url: Özel test URL'i (opsiyonel)
            production_url: Özel production URL'i (opsiyonel)
        """
        self.api_key = api_key
        self.environment = environment
        
        # Özel URL verilmişse onu kullan, yoksa varsayılan
        if environment == 'production' and production_url:
            self.base_url = production_url.rstrip('/')
        elif environment == 'test' and test_url:
            self.base_url = test_url.rstrip('/')
        else:
            self.base_url = self.BASE_URLS.get(environment, self.BASE_URLS['test'])
        
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        """HTTP session'ı yapılandır"""
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json-patch+json',
            'Accept': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, data=None, params=None, timeout=30):
        """Tüm HTTP isteklerini yöneten merkezi metod"""
        url = f"{self.base_url}{endpoint}"
        
        # İstek logla (sadece DEBUG seviyesinde)
        logger.debug(f"Nilvera API İstek: {method} {url}")
        if data:
            try:
                request_json = json.dumps(data, indent=2, ensure_ascii=False)
                logger.debug(f"Nilvera API İstek Body:\\n{request_json}")
            except Exception:
                logger.debug(f"Nilvera API İstek Body: {data}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=timeout
            )
            
            # Yanıt logla (sadece DEBUG seviyesinde)
            logger.debug(f"Nilvera API Yanıt [{response.status_code}]: {endpoint}")
            
            # Başarılı yanıt
            if response.status_code in [200, 201, 204]:
                try:
                    result = response.json() if response.content else {}
                except ValueError:
                    result = response.text
                
                logger.debug(f"Nilvera API Başarılı Yanıt: {str(result)[:500]}")
                return {
                    'success': True,
                    'data': result,
                    'status_code': response.status_code
                }
            
            # Hatalı yanıt
            error_detail = ""
            raw_response = ""
            try:
                raw_response = response.text
                error_data = response.json()
                if isinstance(error_data, dict):
                    error_parts = []
                    for key in ['message', 'Message', 'title', 'Title', 'detail', 'Detail', 'errors', 'Errors']:
                        val = error_data.get(key)
                        if val:
                            error_parts.append(f"{key}: {val}")
                    error_detail = " | ".join(error_parts) if error_parts else str(error_data)
                elif isinstance(error_data, list):
                    error_detail = str(error_data)
                else:
                    error_detail = str(error_data)
            except ValueError:
                error_detail = response.text
                raw_response = response.text

            logger.error(f"Nilvera API Hata [{response.status_code}]: {endpoint}")
            logger.error(f"Nilvera API Hata Detay: {error_detail}")
            
            raise NilveraAPIError(
                error_detail,
                status_code=response.status_code,
                response=raw_response
            )

        except requests.exceptions.Timeout:
            logger.error(f"Nilvera API Timeout: {endpoint}")
            raise NilveraTimeoutError('Bağlantı zaman aşımına uğradı')
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Nilvera API Bağlantı Hatası: {endpoint}")
            raise NilveraConnectionError('Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.')
        
        except NilveraAPIError:
            # Zaten fırlattık, tekrar raise et
            raise
        
        except Exception as e:
            logger.error(f"Nilvera API Genel Hata: {endpoint} - {str(e)}")
            raise

    # ==================== Bağlantı Testi ====================

    def test_connection(self):
        """
        Nilvera API bağlantısını test eder
        
        Returns:
            dict: {'success': bool, 'data': dict, 'status_code': int}
        """
        try:
            return self._make_request('GET', '/general/company')
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': None
            }

    def get_company_info(self):
        """
        Firma bilgilerini getirir
        
        Returns:
            dict: {'success': bool, 'data': dict}
        """
        try:
            return self._make_request('GET', '/general/company')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== Seri İşlemleri ====================

    def get_einvoice_series(self):
        """
        E-Fatura serilerini listeler
        
        Returns:
            dict: {'success': bool, 'data': list}
        """
        try:
            return self._make_request('GET', '/einvoice/Series')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_series_detail(self, series_id):
        """
        Seri detayını getirir
        
        Args:
            series_id: Seri ID'si
        
        Returns:
            dict: Seri detay bilgileri
        """
        try:
            result = self.get_einvoice_series()
            if not result['success']:
                return result
            
            series_list = result.get('data', [])
            if isinstance(series_list, dict):
                series_list = series_list.get('Content', series_list.get('data', []))
            
            for series in series_list:
                if series.get('ID') == series_id or str(series.get('ID')) == str(series_id):
                    current_year = str(datetime.now().year)
                    details = series.get('Details', [])
                    
                    selected_detail = None
                    for detail in details:
                        if str(detail.get('Year', '')) == current_year:
                            selected_detail = detail
                            break
                    
                    if not selected_detail and details:
                        selected_detail = details[-1]
                    
                    return {
                        'success': True,
                        'data': {
                            'series_id': series.get('ID'),
                            'series_name': series.get('Name', ''),
                            'is_default': series.get('IsDefault', False),
                            'is_active': series.get('IsActive', True),
                            'last_used_number': selected_detail.get('OrdinalNumber', 0) if selected_detail else 0,
                            'year': selected_detail.get('Year', current_year) if selected_detail else current_year,
                        }
                    }
            
            return {
                'success': False,
                'error': f'Seri bulunamadı: {series_id}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== E-Fatura İşlemleri ====================

    def create_draft_invoice(self, invoice_data: dict, customer_alias: str = ""):
        """
        E-Fatura taslağı oluşturur
        
        Args:
            invoice_data: Fatura verisi (Nilvera formatında)
            customer_alias: Müşteri alias (ihracat için boş)
        
        Returns:
            dict: {'success': bool, 'data': dict}
        """
        request_body = {
            "EInvoice": invoice_data,
            "CustomerAlias": customer_alias
        }
        
        logger.debug(f"Taslak fatura oluşturuluyor - UUID: {invoice_data.get('InvoiceInfo', {}).get('UUID', '?')}")
        
        try:
            return self._make_request('POST', '/einvoice/Draft/Create', data=request_body)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def confirm_and_send_draft(self, invoice_uuids: list, alias: str = "urn:mail:ihracatpk@gtb.gov.tr"):
        """
        Taslak faturaları onaylayıp gönderir
        
        Args:
            invoice_uuids: Fatura UUID listesi
            alias: Alıcı alias (ihracat için GTB email)
        
        Returns:
            dict: {'success': bool, 'data': dict}
        """
        send_data = [
            {"Alias": alias, "UUID": uid}
            for uid in invoice_uuids
        ]
        
        try:
            return self._make_request('POST', '/einvoice/Draft/ConfirmAndSend', data=send_data)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_invoice_status(self, invoice_uuid: str):
        """
        Fatura durumunu sorgular
        
        Args:
            invoice_uuid: Fatura UUID'si
        
        Returns:
            dict: Fatura durum bilgileri
        """
        try:
            return self._make_request('GET', f'/einvoice/Sale/{invoice_uuid}/Status')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def check_from_gtb(self, invoice_uuid: str):
        """
        GTB'den ihracat durumunu sorgular
        
        Args:
            invoice_uuid: Fatura UUID'si
        
        Returns:
            dict: GTB tescil bilgileri
        """
        try:
            return self._make_request('GET', f'/einvoice/Sale/{invoice_uuid}/CheckFromGtb')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_invoice_details(self, invoice_uuid: str):
        """
        Fatura detayını getirir
        
        Args:
            invoice_uuid: Fatura UUID'si
        
        Returns:
            dict: Fatura detay bilgileri
        """
        try:
            return self._make_request('GET', f'/einvoice/Sale/{invoice_uuid}/Details')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_invoice_pdf(self, invoice_uuid: str, is_draft: bool = False):
        """
        Fatura PDF'ini indirir
        
        Args:
            invoice_uuid: Fatura UUID'si
            is_draft: True ise taslak endpoint kullanılır
        
        Returns:
            dict: {'success': bool, 'data': bytes}
        """
        endpoint_type = "Draft" if is_draft else "Sale"
        url = f"{self.base_url}/einvoice/{endpoint_type}/{invoice_uuid}/pdf"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                # JSON wrapped response mu kontrol et
                if 'application/json' in content_type:
                    try:
                        import base64
                        json_data = response.json()
                        if isinstance(json_data, str):
                            pdf_content = base64.b64decode(json_data)
                        elif isinstance(json_data, dict) and 'data' in json_data:
                            pdf_content = base64.b64decode(json_data['data'])
                        else:
                            pdf_content = response.content
                    except:
                        pdf_content = response.content
                else:
                    pdf_content = response.content
                
                return {
                    'success': True,
                    'data': pdf_content,
                    'content_type': content_type,
                    'size': len(pdf_content)
                }
            
            raise NilveraAPIError(
                f'PDF indirilemedi: HTTP {response.status_code}',
                status_code=response.status_code,
                response=response.text
            )
        
        except NilveraAPIError:
            raise
        except Exception as e:
            raise NilveraConnectionError(str(e))

    def get_invoice_html(self, invoice_uuid: str, is_draft: bool = False):
        """
        Fatura HTML'ini indirir
        
        Args:
            invoice_uuid: Fatura UUID'si
            is_draft: True ise taslak endpoint kullanılır
        
        Returns:
            dict: {'success': bool, 'data': bytes}
        """
        endpoint_type = "Draft" if is_draft else "Sale"
        url = f"{self.base_url}/einvoice/{endpoint_type}/{invoice_uuid}/html"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    try:
                        json_data = response.json()
                        if isinstance(json_data, str):
                            html_content = json_data.encode('utf-8')
                        elif isinstance(json_data, dict) and 'data' in json_data:
                            html_content = json_data['data'].encode('utf-8')
                        else:
                            html_content = response.content
                    except:
                        html_content = response.content
                else:
                    html_content = response.content
                
                return {
                    'success': True,
                    'data': html_content,
                    'content_type': content_type,
                    'size': len(html_content)
                }
            
            raise NilveraAPIError(
                f'HTML indirilemedi: HTTP {response.status_code}',
                status_code=response.status_code,
                response=response.text
            )
        
        except NilveraAPIError:
            raise
        except Exception as e:
            raise NilveraConnectionError(str(e))

    def get_invoice_xml(self, invoice_uuid: str, is_draft: bool = False):
        """
        Fatura XML'ini indirir
        
        Args:
            invoice_uuid: Fatura UUID'si
            is_draft: True ise taslak endpoint kullanılır
        
        Returns:
            dict: {'success': bool, 'data': bytes}
        """
        endpoint_type = "Draft" if is_draft else "Sale"
        url = f"{self.base_url}/einvoice/{endpoint_type}/{invoice_uuid}/xml"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    try:
                        json_data = response.json()
                        if isinstance(json_data, str):
                            xml_content = json_data.encode('utf-8')
                        elif isinstance(json_data, dict) and 'data' in json_data:
                            xml_content = json_data['data'].encode('utf-8')
                        else:
                            xml_content = response.content
                    except:
                        xml_content = response.content
                else:
                    xml_content = response.content
                
                return {
                    'success': True,
                    'data': xml_content,
                    'content_type': content_type,
                    'size': len(xml_content)
                }
            
            raise NilveraAPIError(
                f'XML indirilemedi: HTTP {response.status_code}',
                status_code=response.status_code,
                response=response.text
            )
        
        except NilveraAPIError:
            raise
        except Exception as e:
            raise NilveraConnectionError(str(e))

    def cancel_draft_invoice(self, invoice_uuid: str):
        """
        Taslak faturayı iptal eder
        
        Args:
            invoice_uuid: Fatura UUID'si
        
        Returns:
            dict: {'success': bool}
        """
        try:
            return self._make_request('DELETE', f'/einvoice/draft/{invoice_uuid}')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== Gelen Faturalar ====================

    def get_incoming_invoices(self, start_date: str = None, end_date: str = None, 
                              page: int = 1, page_size: int = 30, search: str = None):
        """
        Gelen faturaları listeler
        
        Args:
            start_date: Başlangıç tarihi (ISO format)
            end_date: Bitiş tarihi (ISO format)
            page: Sayfa numarası
            page_size: Sayfa başına kayıt sayısı
            search: Arama kelimesi
        
        Returns:
            dict: Fatura listesi
        """
        params = {
            'Page': page,
            'PageSize': page_size
        }
        
        if start_date:
            params['StartDate'] = start_date
        if end_date:
            params['EndDate'] = end_date
        if search:
            params['Search'] = search
        
        try:
            return self._make_request('GET', '/einvoice/Purchase', params=params)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_incoming_invoice_details(self, invoice_uuid: str):
        """
        Gelen fatura detayını getirir
        
        Args:
            invoice_uuid: Fatura UUID'si
        
        Returns:
            dict: Fatura detayları
        """
        try:
            return self._make_request('GET', f'/einvoice/Purchase/{invoice_uuid}/Details')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== E-ARŞİV FAT URA ====================
    
    def create_archive_invoice(self, invoice_data: dict):
        """
        E-Arşiv faturası oluşturur
        
        Args:
            invoice_data: E-Arşiv fatura verisi (Nilvera formatında)
        
        Returns:
            dict: {'success': bool, 'data': dict}
        """
        archive_request = {
            "ArchiveInvoice": invoice_data
        }
        
        try:
            return self._make_request('POST', '/earchive/Draft/Create', data=archive_request)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def confirm_and_send_archive_drafts(self, invoice_uuids: list):
        """
        E-Arşiv taslak faturalarını onaylayıp gönderir
        
        Args:
            invoice_uuids: Fatura UUID listesi
        
        Returns:
            dict: {'success': bool, 'data': dict}
        """
        if not invoice_uuids:
            raise ValueError('En az bir fatura UUID\'si gerekli')
        
        try:
            return self._make_request('POST', '/earchive/Draft/ConfirmAndSend', data=invoice_uuids)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_earchive_series(self):
        """
        E-Arşiv serilerini listeler
        
        Returns:
            dict: E-Arşiv seri listesi
        """
        try:
            return self._make_request('GET', '/earchive/Series')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== MÜKELLEF KONTROLÜ ====================
    
    def check_taxpayer_status(self, tax_number: str):
        """
        Vergi numarasına göre e-fatura mükellefiyetini kontrol eder
        
        Args:
            tax_number: Vergi/TC kimlik numarası
        
        Returns:
            dict: Mükellef durumu bilgisi
        """
        try:
            return self._make_request('GET', f'/general/GlobalCompany/GetGlobalCustomerInfo/{tax_number}')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
