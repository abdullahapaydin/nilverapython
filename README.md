# Nilvera Python Client

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

Nilvera E-Fatura ve E-Arşiv REST API için resmi olmayan Python client kütüphanesi.

## Özellikler

- ✅ **İhracat E-Fatura** oluşturma ve gönderme
- ✅ **İç Piyasa E-Fatura** ve **E-Arşiv Fatura** desteği
- ✅ **Otomatik Mükellef Kontrolü** (E-Fatura vs E-Arşiv tespit)
- ✅ **Seri Yönetimi** (Dinamik seri algılama ve numara üretme)
- ✅ Taslak fatura yönetimi
- ✅ Fatura durum sorgulama
- ✅ GTB (Gümrük) entegrasyonu (ihracat için)
- ✅ PDF, HTML, XML formatlarında fatura indirme
- ✅ Gelen fatura yönetimi
- ✅ **Toplu Fatura Gönderimi**
- ✅ **Para Birimi ve Döviz Kuru** desteği
- ✅ TCMB döviz kuru servisi (bonus!)
- ✅ Test ve Production ortam desteği
- ✅ Detaylı hata yönetimi ve loglama
- ✅ Type hints desteği

## Kurulum

### GitHub'dan Kurulum

```bash
# Direkt olarak kurulum
pip install git+https://github.com/abdullahapaydin/nilverapython.git

# veya klonlayarak geliştirici modunda
git clone github.com/abdullahapaydin/nilverapython.git
cd nilverapython
pip install -e .
```

### PyPI'dan Kurulum

```bash
pip install nilvera-client
```

## Hızlı Başlangıç

### Bağlantı Testi

```python
from nilvera_client import NilveraClient

# Test ortamı için
client = NilveraClient(api_key='your-api-key', environment='test')

# Bağlantıyı test et
result = client.test_connection()
if result['success']:
    print("Bağlantı başarılı!")
    print(f"Firma: {result['data']['Name']}")
else:
    print(f"Hata: {result['error']}")
```

### E-Fatura Serileri

```python
# Tüm serileri listele
series = client.get_einvoice_series()
if series['success']:
    for s in series['data']:
        print(f"Seri: {s['Name']} - Aktif: {s['IsActive']}")

# Belirli bir seri detayını al
detail = client.get_series_detail(series_id=123)
if detail['success']:
    print(f"Son kullanılan numara: {detail['data']['last_used_number']}")
```

### Taslak Fatura Oluşturma

```python
invoice_data = {
    "InvoiceInfo": {
        "UUID": "550e8400-e29b-41d4-a716-446655440000",
        "InvoiceType": 2,  # ISTISNA
        "InvoiceProfile": 3,  # IHRACAT
        "InvoiceSerieOrNumber": "IHR",
        "IssueDate": "2026-02-15T10:00:00.000Z",
        "CurrencyCode": "USD",
        "ExchangeRate": 34.50,
        # ... diğer alanlar
    },
    "CompanyInfo": {
        "TaxNumber": "1234567890",
        "Name": "Şirket Adı",
        # ... diğer alanlar
    },
    "ExportCustomerInfo": {
        "LegalRegistrationName": "Customer Name",
        "Country": "USA",
        # ... diğer alanlar
    },
    "InvoiceLines": [
        {
            "Index": "1",
            "Name": "Ürün Adı",
            "Quantity": 100,
            "UnitType": "C62",
            "Price": 10.50,
            # ... diğer alanlar
        }
    ]
}

# Taslak oluştur
result = client.create_draft_invoice(invoice_data)
if result['success']:
    print("Taslak fatura oluşturuldu!")
    
    # Taslağı onayla ve gönder (ihracat için)
    invoice_uuid = invoice_data['InvoiceInfo']['UUID']
    send_result = client.confirm_and_send_draft(
        [invoice_uuid],
        alias="urn:mail:ihracatpk@gtb.gov.tr"  # İhracat için GTB
    )
    
    if send_result['success']:
        print("Fatura gönderildi!")
```

### Mükellef Kontrolü (E-Fatura vs E-Arşiv)

```python
# Müşterinin e-fatura mükellefiyetini kontrol et
tax_number = "1234567890"
result = client.check_taxpayer_status(tax_number)

if result['success']:
    taxpayer_data = result['data']
    
    # E-Fatura mükellefi mi?
    is_taxpayer = taxpayer_data.get('isTaxpayer', False)
    
    if is_taxpayer:
        print("✅ E-Fatura mükellefi - E-Fatura kesilmeli")
        customer_alias = taxpayer_data.get('alias')  # Müşteri alias'ı
        print(f"Müşteri Alias: {customer_alias}")
    else:
        print("❌ E-Fatura mükellefi değil - E-Arşiv kesilmeli")
```

### E-Arşiv Fatura Oluşturma

```python
# E-Arşiv fatura verisi hazırla
archive_invoice = {
    "InvoiceInfo": {
        "UUID": "550e8400-e29b-41d4-a716-446655440001",
        "InvoiceType": "SATIS",
        "InvoiceSerieOrNumber": "CFF",  # E-Arşiv seri
        "IssueDate": "2026-02-15T10:00:00.000Z",
        "CurrencyCode": "TRY",
        "LineExtensionAmount": 100.00,
        "PayableAmount": 120.00,
        "KdvTotal": 20.00,
        # ... diğer alanlar
    },
    "CompanyInfo": {
        # Firma bilgileri
    },
    "CustomerInfo": {
        # Müşteri bilgileri (bireysel müşteri için TaxNumber boş olabilir)
    },
    "InvoiceLines": [
        # Fatura kalemleri
    ]
}

# E-Arşiv fatura oluştur
result = client.create_archive_invoice(archive_invoice)
if result['success']:
    print("E-Arşiv fatura taslağı oluşturuldu!")
    invoice_uuid = result['data']['UUID']
    
    # Taslağı onayla ve gönder
    send_result = client.confirm_and_send_archive_drafts([invoice_uuid])
    if send_result['success']:
        print("E-Arşiv fatura gönderildi!")
```

### E-Fatura Serileri

```python
# E-Fatura serilerini listele
series_result = client.get_einvoice_series()
if series_result['success']:
    for series in series_result['data']:
        print(f"Seri: {series['Name']} - ID: {series['ID']}")

# E-Arşiv serilerini listele
archive_series_result = client.get_earchive_series()
if archive_series_result['success']:
    for series in archive_series_result['data']:
        print(f"E-Arşiv Seri: {series['Name']} - ID: {series['ID']}")
```

### Toplu Fatura Gönderimi

```python
# Birden fazla taslak faturayı toplu gönder
invoice_uuids = [
    "uuid-1",
    "uuid-2",
    "uuid-3"
]

# E-Fatura için (ihracat)
result = client.confirm_and_send_draft(
    invoice_uuids, 
    alias="urn:mail:ihracatpk@gtb.gov.tr"  # İhracat için GTB
)

# E-Fatura için (iç piyasa - müşteri alias'ı ile)
result = client.confirm_and_send_draft(
    invoice_uuids,
    alias="urn:mail:customer@firma.com"  # Müşteri alias'ı
)

# E-Arşiv için
result = client.confirm_and_send_archive_drafts(invoice_uuids)

if result['success']:
    print(f"{len(invoice_uuids)} fatura başarıyla gönderildi!")
```

### Fatura Sorgulama

```python
invoice_uuid = "550e8400-e29b-41d4-a716-446655440000"

# Durum sorgula
status = client.get_invoice_status(invoice_uuid)
print(f"Durum: {status['data']}")

# GTB'den sorgula (ihracat için)
gtb_status = client.check_from_gtb(invoice_uuid)
if gtb_status['success']:
    print(f"Gümrük Tescil No: {gtb_status['data'].get('CustomsRegistrationNumber')}")

# Detayları al
details = client.get_invoice_details(invoice_uuid)
if details['success']:
    print(f"Fatura No: {details['data']['InvoiceNumber']}")
```

### Fatura İndirme

```python
invoice_uuid = "550e8400-e29b-41d4-a716-446655440000"

# PDF indir
pdf_result = client.get_invoice_pdf(invoice_uuid)
if pdf_result['success']:
    with open('fatura.pdf', 'wb') as f:
        f.write(pdf_result['data'])
    print(f"PDF indirildi ({pdf_result['size']} bytes)")

# HTML indir
html_result = client.get_invoice_html(invoice_uuid)
if html_result['success']:
    with open('fatura.html', 'wb') as f:
        f.write(html_result['data'])

# XML indir
xml_result = client.get_invoice_xml(invoice_uuid)
if xml_result['success']:
    with open('fatura.xml', 'wb') as f:
        f.write(xml_result['data'])
```

### Gelen Faturalar

```python
# Son 30 gün
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

result = client.get_incoming_invoices(
    start_date=start_date.isoformat() + '.000Z',
    end_date=end_date.isoformat() + '.999Z',
    page=1,
    page_size=50
)

if result['success']:
    invoices = result['data']['Content']
    print(f"Toplam {len(invoices)} fatura bulundu")
    
    for invoice in invoices:
        print(f"- {invoice['InvoiceNumber']} | {invoice['SenderTitle']}")
```

### TCMB Döviz Kuru Servisi

```python
from nilvera_client import TCMBCurrencyService

# Bugünün USD alış kuru
result = TCMBCurrencyService.get_latest_usd_buy_rate()
if result['success']:
    print(f"USD/TRY: {result['rate']:.4f} ({result['date']})")

# EUR alış kuru
result = TCMBCurrencyService.get_latest_eur_buy_rate()
if result['success']:
    print(f"EUR/TRY: {result['rate']:.4f}")

# Belirli bir tarih için
from datetime import datetime
date = datetime(2026, 1, 15)
result = TCMBCurrencyService.get_exchange_rate('USD', date=date)
```

## Hata Yönetimi

```python
from nilvera_client import (
    NilveraClient,
    NilveraException,
    NilveraConnectionError,
    NilveraTimeoutError,
    NilveraAPIError
)

try:
    client = NilveraClient(api_key='your-key')
    result = client.test_connection()
    
except NilveraConnectionError as e:
    print(f"Bağlantı hatası: {e}")
    
except NilveraTimeoutError as e:
    print(f"Zaman aşımı: {e}")
    
except NilveraAPIError as e:
    print(f"API Hatası [{e.status_code}]: {e}")
    print(f"Ham yanıt: {e.response}")
    
except NilveraException as e:
    print(f"Genel hata: {e}")
```

## Loglama

```python
import logging

# DEBUG seviyesinde detaylı loglar
logging.basicConfig(level=logging.DEBUG)

# Sadece nilvera_client logları
logger = logging.getLogger('nilvera_client')
logger.setLevel(logging.DEBUG)
```

## Production Ortamı

```python
# Production API kullanımı
client = NilveraClient(
    api_key='production-api-key',
    environment='production'
)

# Özel URL (gerekirse)
client = NilveraClient(
    api_key='your-key',
    environment='production',
    production_url='https://custom-api.example.com'
)
```

## Gereksinimler

- Python 3.7+
- requests >= 2.25.0

## Lisans

MIT License - 

## Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır! 

## Destek

- 📧 Email: a.apaydin1986@gmail.com
- 🐛 Issues: https://github.com/abdullahapaydin/nilverapython

## Yasal Uyarı

Bu kütüphane Nilvera tarafından resmi olarak desteklenmemektedir. Kullanımınız tamamen kendi sorumluluğunuzdadır.


**Not:** Bu kütüphane aktif geliştirme aşamasındadır. Production ortamında kullanmadan önce detaylı testler yapmanız önerilir.
