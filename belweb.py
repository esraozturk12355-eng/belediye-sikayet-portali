import streamlit as st
import pandas as pd
import os
import re
import base64
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Portal", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- 📚 TAM KAPSAMLI EVRAK VERİTABANI ---
EVRAK_DATABANK = {
    "Destek Hizmetleri Müdürlüğü": {
        "İhale Dosyası Alımı": ["İmza Sirküleri", "Vezne Alındı Makbuzu", "Faaliyet Belgesi", "Ticaret Sicil Gazetesi", "Dilekçe"],
        "Doğrudan Temin Başvurusu": ["Teklif Mektubu", "Vergi Levhası", "Oda Kayıt Belgesi", "Sabıka Kaydı", "Banka Hesap Bilgileri"],
        "Mal/Hizmet Kabul İşlemleri": ["Fatura Aslı", "Sevk İrsaliyesi", "Muayene Kabul Tutanağı", "Sözleşme Örneği", "Teslim Tesellüm Tutanağı"],
        "Hurda Satış İhalesi": ["Geçici Teminat Dekontu", "Kimlik Fotokopisi", "İkametgah", "Şartname Alındı Makbuzu", "Teklif Zarfı"],
        "Tedarikçi Kaydı": ["Firma Bilgi Formu", "Vergi Levhası", "Yetki Belgesi", "İmza Beyannamesi", "E-posta/KEP Adresi Bilgisi"]
    },
    "Emlak ve İstimlak Müdürlüğü": {
        "Belediye Taşınmazı Kiralama": ["İkametgah", "Adli Sicil Kaydı", "Geçici Teminat Makbuzu", "Kimlik Fotokopisi", "Şartname Onay Yazısı"],
        "Ecrimisil Ödemesi": ["Ödeme Tebligatı", "Kimlik Fotokopisi", "Taşınmaz Bilgi Formu", "Dilekçe", "Emlak Beyanı"],
        "Kira Sözleşmesi Yenileme": ["Mevcut Sözleşme", "Borçsuzluk Yazısı", "Kimlik/İmza Sirküleri", "Dilekçe", "Güncel Adres Beyanı"],
        "Kamulaştırma Bilgi Talebi": ["Tapu Sureti", "Veraset İlamı (Gerekirse)", "Kimlik Fotokopisi", "Dilekçe", "Vekaletname"],
        "Yer Tahsis Talebi": ["Resmi Kurum Yazısı veya Dilekçe", "Kroki", "Kullanım Amacı Belgesi", "Faaliyet Raporu", "Proje Özeti"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol ve Kaldırım Onarım Talebi": ["Konum Bilgisi", "Dilekçe", "Fotoğraflı Kanıt", "İletişim Bilgileri", "Muhtar Yazısı (Opsiyonel)"],
        "Alt Yapı Kazı İzni": ["Proje Onayı", "AYKOME Kararı", "Teminat Dekontu", "İş Programı", "Güvenlik Taahhütnamesi"],
        "Asfalt Katılım Payı Sorgulama": ["Tapu Fotokopisi", "Kimlik Bilgisi", "Emlak Beyanı", "Dilekçe", "Belediye Sicil No"],
        "Moloz Atım İzni": ["Atık Miktarı Beyanı", "Adres Bilgisi", "Harç Makbuzu", "Dilekçe", "Nakliye Araç Plakası"],
        "Yağmur Suyu Hattı Bağlantısı": ["Bina Vaziyet Planı", "Kanal Kot Tutanağı", "Dilekçe", "Tapu Kaydı", "Ruhsat Fotokopisi"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Bildirimi": ["Tapu Fotokopisi", "Kimlik Fotokopisi", "Kısıtlılık Belgesi", "Dilekçe", "Rayiç Bedel Yazısı"],
        "Rayiç Bedel Belgesi": ["Tapu Kaydı", "Kimlik Fotokopisi", "Borçsuzluk Yazısı", "Dilekçe", "Vekaletname"],
        "İlan ve Reklam Vergisi": ["Tabela Ölçüleri", "Vergi Levhası", "Tabela Fotoğrafı", "Dilekçe", "Kira Kontratı"],
        "Çevre Temizlik Vergisi": ["Kira Kontratı", "Vergi Levhası", "Su Faturası Örneği", "Kimlik", "Dilekçe"],
        "Borç Yapılandırma": ["Başvuru Formu", "Kimlik Fotokopisi", "Taahhütname", "Vekaletname (Gerekirse)", "Ödeme Planı Seçimi"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kaydı": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi", "Çip Numarası", "Sahip Kimlik Fotokopisi", "İkametgah"],
        "İlaçlama Talebi": ["Adres Bilgisi", "Dilekçe", "Apartman Karar Defteri (Gerekirse)", "Kimlik Bilgisi", "İletişim"],
        "Sokak Hayvanı Tedavi": ["Konum", "Fotoğraf/Video", "İhbar Dilekçesi", "İrtibat No", "Olay Saati Bilgisi"],
        "Petshop Denetim Belgesi": ["İşyeri Ruhsatı", "Eğitim Sertifikası", "Hijyen Belgesi", "Dilekçe", "Tarım İlçe Onayı"],
        "Hayvansal Atık İmhası": ["Atık Teslim Tutanağı", "İşletme Belgesi", "Dilekçe", "Araç Bilgisi", "Miktar Beyanı"]
    },
    "Yapı Kontrol Müdürlüğü": {
        "Yıkım Kararı Sorgulama": ["Tapu Kaydı", "Ada/Parsel Bilgisi", "Kimlik Fotokopisi", "Dilekçe", "Vekaletname"],
        "Kaçak Yapı İhbar": ["Konum Bilgisi", "Fotoğraf", "İhbar Dilekçesi (İsimli/İsimsiz)", "Kroki", "Varsa Tapu No"],
        "Bina Enerji Kimlik Belgesi": ["Yapı Kullanma İzni", "Mimari Proje", "Isı Yalıtım Raporu", "Dilekçe", "Müteahhit Bilgileri"],
        "Statik Rapor Talebi": ["Mimari Proje", "Zemin Etüdü", "Bina Fotoğrafları", "Dilekçe", "Tapu Sureti"],
        "Riskli Yapı Tespiti": ["Tapu Aslı", "Kimlik Fotokopisi", "Nüfus Kayıt Örneği", "Dilekçe", "Bina Ortak Karar Protokolü"]
    },
    "Yazı İşleri Müdürlüğü": {
        "Nikah Başvurusu": ["Sağlık Raporu", "4 Adet Fotoğraf", "Kimlik Aslı", "Nüfus Kayıt Örneği", "Bekarlık Belgesi"],
        "Encümen Kararı Örneği": ["Dilekçe", "Karar Tarih ve Sayısı", "Kimlik Fotokopisi", "İlgili Evrak Aslı", "Vekaletname"],
        "Meclis Kararı Sorgulama": ["Dilekçe", "Konu Özeti", "Tarih Aralığı", "Kimlik", "İletişim"],
        "Gelen Evrak Takibi": ["Kayıt Numarası", "Başvuru Tarihi", "Kimlik", "Dilekçe Konusu", "Telefon"],
        "Asker Ailesi Yardımı": ["Askerlik Belgesi", "Vukuatlı Nüfus Kayıt Örneği", "Fakirlik Belgesi", "İkametgah", "Kimlik"]
    },
    "Zabıta Müdürlüğü": {
        "İşyeri Açma Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "İtfaiye Raporu", "Oda Kaydı", "Ustalık Belgesi"],
        "Pazar Yeri Tahsisi": ["Oda Kayıt Belgesi", "Sabıka Kaydı", "Kimlik", "2 Fotoğraf", "İkametgah"],
        "Hafta Tatili Ruhsatı": ["Mevcut Ruhsat", "Harç Makbuzu", "Dilekçe", "Vergi Levhası", "Kimlik"],
        "Canlı Müzik İzni": ["Çevresel Gürültü Raporu", "İşyeri Ruhsatı", "Dilekçe", "Akustik Rapor", "Başvuru Formu"],
        "Seyyar Satıcı Başvurusu": ["Fakirlik Belgesi", "Sabıka Kaydı", "Sağlık Raporu", "İkametgah", "Dilekçe"]
    },
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": {
        "Atık Yağ Toplama Talebi": ["Adres Bilgisi", "Atık Miktarı", "İletişim", "Dilekçe", "Firma Bilgisi"],
        "Geri Dönüşüm Kutusu Talebi": ["Adres/Konum", "Bina/Site Yönetim Kararı", "Dilekçe", "İletişim", "Kişi Sayısı Beyanı"],
        "Sıfır Atık Belgesi Başvurusu": ["Faaliyet Belgesi", "Atık Beyan Formu", "Eğitim Tutanakları", "Ekipman Listesi", "Dilekçe"],
        "Elektronik Atık Bildirimi": ["Eşya Listesi", "Adres", "Telefon", "Dilekçe", "Fotoğraf"],
        "Kompost Üretim Desteği": ["Başvuru Formu", "Alan Bilgisi", "Kimlik", "Dilekçe", "Eğitim Katılım Belgesi"]
    },
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı": ["Tapu Kaydı", "Mimari Proje", "İmar Durum Belgesi", "Aplikasyon Krokisi", "Zemin Etüdü"],
        "Yapı Kullanma İzin Belgesi": ["Enerji Kimliği", "Sığınak Onayı", "SGK İlişiksiz Belgesi", "İtfaiye Uygunluk", "Asansör Tescil"],
        "Numarataj İşlemleri": ["Tapu Fotokopisi", "Kimlik", "Yapı Ruhsatı", "Dilekçe", "Fotoğraf"],
        "Yıkım Ruhsatı": ["Yıkım Planı", "İlgili Kurum Kesme Yazıları", "Dilekçe", "Tapu", "Müteahhit Belgesi"],
        "İmar Planı Değişikliği": ["Gerekçe Raporu", "Tapu Kayıtları", "Vaziyet Planı", "Vekaletname", "Dilekçe"]
    }
}

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap", "Mudurluk_Dosya"]
    if os.path.exists("mesajlar.csv"):
        try: 
            df = pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
            for col in cols:
                if col not in df.columns: df[col] = "Yok"
            return df
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def tel_temizle(tel):
    tel = str(tel).strip()
    if tel.startswith("0"): return tel[1:]
    return tel

def dosya_indirme_linki(dosya_verisi, dosya_adi, etiket="İndir"):
    b64 = base64.b64encode(dosya_verisi).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:4px 8px; border-radius:4px; font-size:12px;">📩 {etiket}: {dosya_adi}</a>'

# MÜDÜRLÜKLER VE TÜRLER
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + list(EVRAK_DATABANK.keys()) + [
    "Emlak ve İstimlak Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", 
    "Destek Hizmetleri Müdürlüğü", "Yapı Kontrol Müdürlüğü"
])))

# --- SESSION STATE ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Akıllı Vatandaş Portalı")
st.divider()

# --- 🤖 1. SAYFA: ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("📝 Talep ve Öneri Bildir"): st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Sorgulama & Sohbet"): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("📄 Gerekli Evraklar Rehberi"): st.session_state.sayfa = "evrak_ekrani"; st.rerun()
    if col4.button("🏢 Müdürlükle İletişime Geç"): st.session_state.sayfa = "iletisim_kanali"; st.rerun()

# --- 📝 2. SAYFA: TALEP FORMU (İstediğin Format) ---
elif st.session_state.sayfa == "talep_ekrani":
    st.markdown("### 📝 Yeni Şikayet Formu")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız", key="ad_yeni")
            eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = False
            if eposta != "": 
                if re.match(email_pattern, eposta, re.IGNORECASE):
                    st.success("E-posta formatı geçerli. ✅")
                    is_email_valid = True
                else: st.warning("⚠️ Lütfen geçerli bir e-posta adresi giriniz!")

        with c2: 
            soyad = st.text_input("Soyadınız", key="soyad_yeni")
            telefon_input = st.text_input("Telefon Numaranız", key="tel_yeni")
        
        secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler, key="mud_yeni")
        tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Bilgi Edinme", "Diğer"])
        sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi, key="tur_yeni")
        detay = st.text_area("Şikayet Detayı", key="detay_yeni")
        
        if st.button("Şikayeti Kaydet"):
            if ad and soyad and eposta and is_email_valid and telefon_input:
                temiz_tel = tel_temizle(telefon_input)
                df_mevcut = veri_yukle()
                yeni_sira_no = 1
                if not df_mevcut.empty and "Müdürlük" in df_mevcut.columns and "Sıra_No" in df_mevcut.columns:
                    birim_kayitlari = df_mevcut[df_mevcut["Müdürlük"] == secilen_mudurluk]
                    if not birim_kayitlari.empty:
                        yeni_sira_no = int(birim_kayitlari["Sıra_No"].max()) + 1
                
                sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni_kayit = {
                    "ID": sikayet_id, "Sıra_No": yeni_sira_no, 
                    "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                    "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": temiz_tel,
                    "Müdürlük": secilen_mudurluk, "Tür": sikayet_turu,
                    "Detay": detay.replace(",", " "), "Durum": "İnceleniyor",
                    "Belediye_Cevabi": "Henüz cevaplanmadı"
                }
                pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"✅ Şikayetiniz başarıyla alınmıştır. Takip ID: {sikayet_id}")
                st.balloons()
            else: st.error("Lütfen formu eksiksiz ve doğru formatta doldurunuz.")

# --- 📄 3. SAYFA: EVRAK REHBERİ ---
elif st.session_state.sayfa == "evrak_ekrani":
    st.markdown("### 📄 Gerekli Evraklar Rehberi")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    m_sec = st.selectbox("Müdürlük Seçiniz:", ["Seçiniz..."] + sorted(list(EVRAK_DATABANK.keys())))
    if m_sec != "Seçiniz...":
        i_sec = st.selectbox("İşlem Seçiniz:", list(EVRAK_DATABANK[m_sec].keys()))
        if i_sec:
            st.info(f"📋 **{i_sec}** için istenen belgeler:")
            for b in EVRAK_DATABANK[m_sec][i_sec]: st.write(f"✅ {b}")

# --- 🔍 4. SAYFA: SORGULAMA (İstediğin Format) ---
elif st.session_state.sayfa == "sorgu_ekrani":
    st.markdown("### 🔍 Şikayet Sorgulama")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz", key="sorgu_input")
    if arama:
        temiz_arama = tel_temizle(arama)
        df = veri_yukle()
        if not df.empty:
            df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
            sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == temiz_arama)]
            if not sonuclar.empty:
                st.info(f"Toplam {len(sonuclar)} adet kaydınız bulundu:")
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            else: st.warning("⚠️ Bu bilgilere ait bir şikayet kaydı bulunamadı.")
        else: st.warning("⚠️ Sistemde henüz kayıtlı şikayet bulunmuyor.")

# --- 🏢 5. SAYFA: İLETİŞİM ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlüğe Belge / Mesaj Gönder")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("msg_form"):
        k_mud = st.selectbox("Birim:", tum_birimler)
        k_mail = st.text_input("E-posta:")
        k_sifre = st.text_input("Şifre Belirleyin:", type="password")
        k_msg = st.text_area("Mesajınız:")
        k_file = st.file_uploader("Belge Ekle:")
        if st.form_submit_button("Gönder"):
            fn = "Yok"
            if k_file:
                if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                fn = f"{datetime.now().strftime('%H%M%S')}_{k_file.name}"
                with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(k_file.getbuffer())
            yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_msg, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}
            pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
            st.success("İletildi!")

# --- 🏢 MÜDÜRLÜK PANELİ (İstediğin Format) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili Girişi)"):
    cp1, cp2 = st.columns(2)
    with cp1: admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
    with cp2: sifre = st.text_input("Şifre:", type="password", key="adm_pass")
    
    if sifre == "1234":
        df_admin = veri_yukle()
        if not df_admin.empty:
            if "Müdürlük" in df_admin.columns:
                filtreli = df_admin[df_admin["Müdürlük"] == admin_birim].sort_values(by="Sıra_No")
                if not filtreli.empty:
                    st.dataframe(filtreli[["Sıra_No", "ID", "Tarih", "Ad", "Soyad", "Telefon", "Durum", "Detay", "Belediye_Cevabi"]])
                    st.write("---")
                    secilen_id = st.selectbox("İşlem Yapılacak ID Seçiniz:", filtreli["ID"].tolist(), key="islem_id")
                    ci1, ci2 = st.columns(2)
                    with ci1:
                        yeni_durum = st.selectbox("Durum Güncelle:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"], key="durum_up")
                        yonlendir = st.selectbox("Başka Birime Yönlendir:", tum_birimler, index=tum_birimler.index(admin_birim), key="yonlendir_up")
                    with ci2: cevap_notu = st.text_area("Cevap Notu:", key="cevap_up")
                    
                    if st.button("Değişiklikleri Onayla"):
                        idx = df_admin[df_admin["ID"] == secilen_id].index
                        if not idx.empty:
                            if df_admin.at[idx[0], "Müdürlük"] != yonlendir:
                                hedef = df_admin[df_admin["Müdürlük"] == yonlendir]
                                df_admin.at[idx[0], "Sıra_No"] = 1 if hedef.empty else hedef["Sıra_No"].max() + 1
                            df_admin.at[idx[0], "Durum"] = yeni_durum
                            df_admin.at[idx[0], "Müdürlük"] = yonlendir
                            df_admin.at[idx[0], "Belediye_Cevabi"] = cevap_notu
                            df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                            st.success("Kayıt başarıyla güncellendi!"); st.rerun()
                else: st.info(f"{admin_birim} için henüz kayıtlı bir şikayet bulunmuyor.")
