import streamlit as st
import re

# Sayfa Ayarları
st.set_page_config(page_title="Ondokuzmayıs Belediyesi", layout="centered")

# Başlık ve Logo
st.title("🏛️ Ondokuzmayıs Belediyesi")
st.subheader("Şikayet Yönetim Portalı")

# Şikayetleri saklamak için (Gerçek projede veritabanı olur, şimdilik geçici hafıza)
if 'sikayet_listesi' not in st.session_state:
    st.session_state.sikayet_listesi = []

# Yan Menü (Sidebar)
menu = st.sidebar.radio("İşlem Seçiniz", ["Yeni Şikayet Oluştur", "Şikayetlerimi Görüntüle"])

if menu == "Yeni Şikayet Oluştur":
    st.header("📝 Yeni Şikayet Formu")

    col1, col2 = st.columns(2)
    with col1:
        ad = st.text_input("Adınız")
        eposta = st.text_input("E-posta Adresiniz")
    with col2:
        soyad = st.text_input("Soyadınız")
        telefon = st.text_input("Telefon Numaranız (10-11 haneli)")

    mudurlukler = [
        "Yazı İşleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Mali Hizmetler Müdürlüğü",
        "Veteriner İşleri Müdürlüğü", "İmar ve Şehircilik Müdürlüğü",
        "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "Fen İşleri Müdürlüğü",
        "Destek Hizmetleri Müdürlüğü", "Zabıta Müdürlüğü", "Yapı Kontrol Müdürlüğü"
    ]

    secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", mudurlukler)

    # Müdürlüğe göre şikayet türleri (Senin sözlük yapın)
    sikayet_turleri_dict = {
        "Yazı İşleri Müdürlüğü": ["Evrak işlemlerinin yavaş ilerlemesi", "Bilgi eksikliği", "Diğer"],
        "Veteriner İşleri Müdürlüğü": ["Sokak hayvanlarının fazlalığı", "Yaralı hayvan", "Aşılama talebi", "Diğer"],
        "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Altyapı sorunu", "Diğer"],
        "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Kaçak satış", "Diğer"],
        # Diğerlerini buraya ekleyebilirsin...
    }

    # Eğer müdürlük sözlükte yoksa genel bir liste verelim
    tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Diğer"])
    sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi)

    adres = st.text_area("Adres Bilgisi")

    # --- EK SORULAR (DINAMIK KISIM) ---
    detay = f"Tür: {sikayet_turu} | Adres: {adres}"

    if sikayet_turu == "Sokak hayvanlarının fazlalığı":
        sayi = st.number_input("Tahmini hayvan sayısı", min_value=1)
        detay += f" | Sayı: {sayi}"

    elif sikayet_turu == "Yaralı hayvan":
        h_tur = st.text_input("Hayvan Türü (Kedi, Köpek vb.)")
        durum = st.radio("Durumu", ["Hafif", "Ağır"])
        detay += f" | Tür: {h_tur} | Durum: {durum}"

    elif sikayet_turu == "Gürültü":
        saat = st.text_input("Gürültü Saat Aralığı")
        detay += f" | Saat: {saat}"

    elif sikayet_turu == "Diğer":
        ek_aciklama = st.text_input("Lütfen detaylı açıklama yazınız")
        detay = f"{ek_aciklama} | Adres: {adres}"

    if st.button("Şikayeti Kaydet"):
        # Basit doğrulama
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", eposta):
            st.error("Lütfen geçerli bir e-posta giriniz!")
        elif not re.match(r"^\d{10,11}$", telefon):
            st.error("Lütfen geçerli bir telefon giriniz!")
        else:
            yeni_kayit = {
                "eposta": eposta,
                "telefon": telefon,
                "mudurluk": secilen_mudurluk,
                "detay": detay,
                "durum": "İnceleniyor"
            }
            st.session_state.sikayet_listesi.append(yeni_kayit)
            st.success("Şikayetiniz başarıyla sisteme kaydedildi!")

elif menu == "Şikayetlerimi Görüntüle":
    st.header("🔍 Şikayet Sorgulama")
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz")

    if arama:
        sonuclar = [s for s in st.session_state.sikayet_listesi if s["eposta"] == arama or s["telefon"] == arama]

        if sonuclar:
            for s in sonuclar:
                with st.expander(f"Müdürlük: {s['mudurluk']} - Durum: {s['durum']}"):
                    st.write(f"**Detaylar:** {s['detay']}")
        else:
            st.warning("Kayıt bulunamadı.")

# --- MÜDÜRLÜK YÖNETİM PANELİ (ŞİFRELİ) ---
st.divider() 
st.subheader("🏢 Müdürlük Yönetim Paneli")

# Tüm müdürlüklerin listesi
mudurluk_listesi = [
    "Yazı İşleri Müdürlüğü", "Emlak ve İstimlak Müdürlüğü", "Mali Hizmetler Müdürlüğü",
    "Veteriner İşleri Müdürlüğü", "İmar ve Şehircilik Müdürlüğü",
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü", "Fen İşleri Müdürlüğü",
    "Destek Hizmetleri Müdürlüğü", "Zabıta Müdürlüğü", "Yapı Kontrol Müdürlüğü"
]

# Giriş Alanları
col1, col2 = st.columns(2)
with col1:
    secilen_mudurluk = st.selectbox("Müdürlük Seçin:", mudurluk_listesi)
with col2:
    sifre = st.text_input("Giriş Şifresi:", type="password")

# Örnek bir şifre belirleyelim (İstersen değiştirebilirsin)
DOGRU_SIFRE = "1234" 

if st.button("Şikayetleri Listele"):
    if sifre == DOGRU_SIFRE:
        try:
            df = pd.read_csv("sikayetler.csv")
            # Seçilen müdürlüğe göre filtrele
            filtreli_df = df[df["Müdürlük"] == secilen_mudurluk]
            
            if not filtreli_df.empty:
                st.success(f"{secilen_mudurluk} birimine ait {len(filtreli_df)} kayıt bulundu.")
                st.table(filtreli_df) # Daha düzenli görünmesi için tablo formatı
            else:
                st.info(f"{secilen_mudurluk} için henüz bir kayıt yok.")
        except FileNotFoundError:
            st.error("Henüz sisteme hiç şikayet girilmemiş.")
    else:
        st.error("Hatalı şifre! Lütfen tekrar deneyin.")
