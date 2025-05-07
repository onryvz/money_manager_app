# 💰 Money Manager Web App

Kişisel gelir-gider ve bütçe takibini kolaylaştırmak için geliştirilmiş, Excel tabanlı verilerden beslenen bir Flask web uygulaması.

---

## 🚀 Özellikler

- 📥 Excel dosyasından (`money-manager.xlsx`) veri aktarımı
- 📊 Anasayfada gelir-gider grafiği (Chart.js)
- ✅ İşlem ekleme, düzenleme ve silme
- 📂 Hesap ve kategori yönetimi
- 🎨 Temiz, sade ve responsive kullanıcı arayüzü

---

## 🧰 Kullanılan Teknolojiler

- Python 3.x
- Flask
- Jinja2
- SQLAlchemy (SQLite)
- Pandas + openpyxl
- Chart.js

---

## 🗂️ Proje Yapısı

```
money_manager_app/
│
├── app.py                  # Ana Flask uygulaması
├── models.py               # Veritabanı modelleri
├── routes.py               # Route tanımlamaları
├── utils/
│   └── load_excel.py       # Excel'den veritabanına veri yükleyici
│
├── templates/
│   ├── base.html           # Tüm sayfaların temel şablonu
│   ├── dashboard.html      # Anasayfa
│   ├── transactions.html   # İşlem listesi
│   └── ...                 
│
├── static/
│   ├── css/
│   ├── js/
│   └── img/
│
├── money-manager.xlsx      # Örnek Excel dosyası
└── README.md
```

---

## ⚙️ Kurulum

1. Depoyu klonla:

```bash
git clone https://github.com/kullaniciadi/money-manager-app.git
cd money-manager-app
```

2. Sanal ortam oluştur ve bağımlılıkları yükle:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Excel verilerini veritabanına yükle:

```bash
python -m utils.load_excel
```

4. Uygulamayı başlat:

```bash
flask run
```

---

## 📌 Yol Haritası

- [x] Excel verilerinin yüklenmesi
- [x] İşlem yönetimi (CRUD)
- [x] Grafik gösterimi
- [ ] Bütçe modülü
- [ ] Hedef modülü
- [ ] Gelişmiş grafikler ve raporlar
- [ ] Kullanıcı desteği
- [ ] Yayınlama (cloud)

---

## 📄 Lisans

MIT Lisansı. İstediğiniz gibi kullanabilir, geliştirebilir ve paylaşabilirsiniz.

---

## 🧑‍💻 Katkı

Pull request'ler açıktır! Sorun bildir veya katkıda bulun.