"""
Nilvera Python Client - Örnek Kullanımlar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bu dosya Nilvera Client'ın çeşitli kullanım örneklerini içerir.
"""

from nilvera_client import NilveraClient, TCMBCurrencyService
from datetime import datetime

# API KEY'inizi buraya yazın (test için)
API_KEY = "your-api-key-here"


def example_connection_test():
    """Bağlantı testi örneği"""
    print("\\n=== Bağlantı Testi ===")
    
    client = NilveraClient(api_key=API_KEY, environment='test')
    result = client.test_connection()
    
    if result['success']:
        print("✅ Bağlantı başarılı!")
        print(f"Firma: {result['data'].get('Name', 'N/A')}")
        print(f"VKN: {result['data'].get('TaxNumber', 'N/A')}")
    else:
        print(f"❌ Hata: {result.get('error')}")


def example_list_series():
    """Fatura serilerini listeleme örneği"""
    print("\\n=== Fatura Serileri ===")
    
    client = NilveraClient(api_key=API_KEY, environment='test')
    result = client.get_einvoice_series()
    
    if result['success']:
        series_list = result['data']
        if isinstance(series_list, dict):
            series_list = series_list.get('Content', [])
        
        print(f"Toplam {len(series_list)} seri bulundu:")
        for series in series_list[:5]:  # İlk 5 seriyi göster
            print(f"  - {series['Name']} (ID: {series['ID']}) - Aktif: {series['IsActive']}")
    else:
        print(f"❌ Hata: {result.get('error')}")


def example_currency_service():
    """TCMB döviz kuru servisi örneği"""
    print("\\n=== TCMB Döviz Kurları ===")
    
    # USD Alış kuru
    usd_result = TCMBCurrencyService.get_latest_usd_buy_rate()
    if usd_result['success']:
        print(f"✅ USD/TRY Alış: {usd_result['rate']:.4f} TRY")
        print(f"   Tarih: {usd_result['date']}")
    else:
        print(f"❌ USD Hatası: {usd_result['error']}")
    
    # EUR Alış kuru
    eur_result = TCMBCurrencyService.get_latest_eur_buy_rate()
    if eur_result['success']:
        print(f"✅ EUR/TRY Alış: {eur_result['rate']:.4f} TRY")
        print(f"   Tarih: {eur_result['date']}")
    else:
        print(f"❌ EUR Hatası: {eur_result['error']}")


def example_create_draft_invoice():
    """Taslak fatura oluşturma örneği (sadece yapı gösterimi)"""
    print("\\n=== Taslak Fatura Oluşturma (Örnek Yapı) ===")
    
    import uuid
    
    invoice_data = {
        "InvoiceInfo": {
            "UUID": str(uuid.uuid4()),
            "InvoiceType": 2,  # ISTISNA
            "InvoiceProfile": 3,  # IHRACAT
            "InvoiceSerieOrNumber": "IHR",
            "IssueDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "CurrencyCode": "USD",
            "ExchangeRate": 34.50,
            "LineExtensionAmount": 1050.00,
            "PayableAmount": 1050.00,
            "KdvTotal": 0.0,
        },
        "CompanyInfo": {
            "TaxNumber": "1234567890",
            "Name": "Örnek Şirket A.Ş.",
            "TaxOffice": "Kozyatağı",
            "Address": "Örnek Cad. No:123",
            "City": "İstanbul",
            "Country": "Türkiye",
        },
        "ExportCustomerInfo": {
            "LegalRegistrationName": "Example Company Inc.",
            "Country": "USA",
            "Address": "123 Main St",
            "City": "New York",
        },
        "InvoiceLines": [
            {
                "Index": "1",
                "Name": "Ürün Adı",
                "Description": "Ürün Açıklaması",
                "Quantity": 100.0,
                "UnitType": "C62",  # Adet
                "Price": 10.50,
                "KDVPercent": 0,
                "KDVTotal": 0.0,
                "Taxes": [
                    {
                        "TaxCode": "0015",
                        "Total": 0.0,
                        "Percent": 0,
                        "ReasonCode": "301",
                        "ReasonDesc": "Mal ihracatı (KDVK 11/1-a)"
                    }
                ],
                "DeliveryInfo": {
                    "GTIPNo": "84212100",
                    "DeliveryTermCode": "EXW",
                    "TransportModeCode": "3",
                }
            }
        ],
        "Notes": ["Bu bir test faturasıdır."]
    }
    
    print("Fatura veri yapısı hazır:")
    print(f"  UUID: {invoice_data['InvoiceInfo']['UUID']}")
    print(f"  Para Birimi: {invoice_data['InvoiceInfo']['CurrencyCode']}")
    print(f"  Toplam: {invoice_data['InvoiceInfo']['PayableAmount']} USD")
    print(f"  Kalem Sayısı: {len(invoice_data['InvoiceLines'])}")
    print("\\n⚠️  Gerçek API çağrısı yapmak için client.create_draft_invoice(invoice_data) kullanın")


def example_incoming_invoices():
    """Gelen faturaları listeleme örneği"""
    print("\\n=== Gelen Faturalar ===")
    
    client = NilveraClient(api_key=API_KEY, environment='test')
    
    # Son 7 günün faturaları
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    result = client.get_incoming_invoices(
        start_date=start_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        end_date=end_date.strftime("%Y-%m-%dT23:59:59.999Z"),
        page=1,
        page_size=10
    )
    
    if result['success']:
        data = result['data']
        if isinstance(data, dict):
            invoices = data.get('Content', [])
            total = data.get('TotalCount', 0)
            print(f"Toplam {total} fatura bulundu (ilk 10 gösteriliyor):")
            
            for inv in invoices[:10]:
                print(f"  - {inv.get('InvoiceNumber', 'N/A')} | {inv.get('SenderTitle', 'N/A')}")
        else:
            print(f"Fatura listesi: {data}")
    else:
        print(f"❌ Hata: {result.get('error')}")


def main():
    """Tüm örnekleri çalıştır"""
    print("=" * 60)
    print("Nilvera Python Client - Örnekler")
    print("=" * 60)
    
    try:
        # Bağlantı testi
        example_connection_test()
        
        # Seri listesi
        example_list_series()
        
        # TCMB döviz kurları (API KEY gerektirmez)
        example_currency_service()
        
        # Taslak fatura yapısı
        example_create_draft_invoice()
        
        # Gelen faturalar
        # example_incoming_invoices()  # Yorumu kaldırarak aktifleştirin
        
    except Exception as e:
        print(f"\\n❌ Genel Hata: {e}")
        import traceback
        traceback.print_exc()
    
    print("\\n" + "=" * 60)
    print("Örnekler tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()
