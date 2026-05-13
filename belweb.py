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
        "Yer Tahsis Talebi": ["Resmi Kurum Yazısı veya Dilekçe", "Kullanım Amacı Belgesi", "Faaliyet Raporu", "Proje Özeti"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol ve Kaldırım Onarım Talebi": ["Konum Bilgisi", "Dilekçe", "Fotoğraflı Kanıt", "İletişim Bilgileri", "Muhtar Yazısı"],
        "Alt Yapı Kazı İzni": ["Proje Onayı", "AYKOME Kararı", "Teminat Dekontu", "İş Programı", "Güvenlik Taahhütnamesi"],
        "Asfalt Katılım Payı Sorgulama": ["Tapu Fotokopisi", "Kimlik Bilgisi", "Emlak Beyanı", "Dilekçe", "Belediye Sicil No"],
        "Moloz Atım İzni": ["Atık Miktarı Beyanı", "Adres Bilgisi", "Harç Makbuzu", "Dilekçe", "Nakliye Araç Plakası"],
        "Yağmur Suyu Hattı Bağlantısı": ["Bina Vaziyet Planı", "Kanal Kot Tutanağı", "Dilekçe", "Tapu Kaydı", "Ruhsat Fotokopisi"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Bildirimi": ["Tapu Fotokopisi", "Kimlik Fotokopisi", "Kısıtlılık Belgesi", "Dilekçe", "Rayiç Bedel Yazısı"],
        "Rayiç Bedel Belgesi": ["Tapu Kaydı", "Kimlik Fotokopisi", "Borçsuzluk Yazısı", "Dilekçe", "Vekaletname"],
        "İlan ve Reklam Vergisi": ["Tabela Ölçüleri", "Vergi Levhası Fotokopisi", "Tabela Fotoğrafı", "Dilekçe", "Kira Kontratı"],
        "Çevre Temizlik Vergisi": ["Kira Kontratı", "Vergi Levhası", "Su Faturası Örneği", "Kimlik", "Dilekçe"],
        "Borç Yapılandırma": ["Başvuru Formu", "Kimlik Fotokopisi", "Taahhütname", "Vekaletname", "Ödeme Planı Seçimi"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kaydı": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi", "Çip Numarası", "Sahip Kimlik Fotokopisi", "İkametgah"],
        "İlaçlama Talebi": ["Adres Bilgisi", "Dilekçe", "Apartman Karar Defteri", "Kimlik Bilgisi", "İletişim"],
        "Sokak Hayvanı Tedavi": ["Konum", "Fotoğraf/Video", "İhbar Dilekçesi", "İrtibat No", "Olay Saati Bilgisi"],
        "Petshop Denetim Belgesi": ["İşyeri Ruhsatı", "Eğitim Sertifikası", "Hijyen Belgesi", "Dilekçe", "Tarım İlçe Onayı"],
        "Hayvansal Atık İmhası": ["Atık Teslim Tutanağı", "İşletme Belgesi", "Dilekçe", "Araç Bilgisi", "Miktar Beyanı"]
    },
    "Yapı Kontrol Müdürlüğü": {
        "Yıkım Kararı Sorgulama": ["Tapu Kaydı", "Ada/Parsel Bilgisi", "Kimlik Fotokopisi", "Dilekçe", "Vekaletname"],
        "Kaçak Yapı İhbar": ["Konum Bilgisi", "Fotoğraf", "İhbar Dilekçesi", "Kroki", "Varsa Tapu No"],
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

# --- REGEX DESENLERİ ---
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive|edu|gov|net)\.(com|com\.tr|net|org)$'
PHONE_PATTERN = r'^(0?)[5][0-9]{9}$'

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Telefon", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap", "Mudurluk_Dosya"]
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

def dosya_indirme_linki(dosya_yolu, dosya_adi, etiket="İndir"):
    if not os.path.exists(dosya_yolu): return "⚠️ Belge yok"
    with open(dosya_yolu, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:4px 8px; border-radius:4px; font-size:12px;">📩 {etiket}: {dosya_adi}</a>'

tum_birimler = sorted(list(EVRAK_DATABANK.keys()))
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}

# --- SESSION STATE ---
if "portal_modu" not in st.session_state: st.session_state.portal_modu = "karşılama"
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Dijital Hizmet Portalı")
st.divider()

# --- 🚀 GİRİŞ EKRANI ---
if st.session_state.portal_modu == "karşılama":
    st.markdown("<h2 style='text-align: center;'>Lütfen Giriş Türünü Seçiniz</h2>", unsafe_allow_html=True)
    st.write("---")
    col_v, col_m = st.columns(2)
    with col_v:
        st.markdown("### 👤 Vatandaş Portalı")
        if st.button("Vatandaş Girişi", use_container_width=True):
            st.session_state.portal_modu = "vatandas"
            st.rerun()
    with col_m:
        st.markdown("### 🏢 Müdürlük Paneli")
        if st.button("Yetkili Girişi", use_container_width=True, type="primary"):
            st.session_state.portal_modu = "mudurluk"
            st.rerun()

# --- 👤 VATANDAŞ ---
elif st.session_state.portal_modu == "vatandas":
    if st.sidebar.button("🏠 Ana Sayfaya Dön"):
        st.session_state.portal_modu = "karşılama"
        st.rerun()
        
    if st.session_state.sayfa == "asistan":
        st.markdown("### 🤖 Akıllı Asistan")
        col1, col2, col3, col4 = st.columns(4)
        if col1.button("📝 Talep Oluştur"): st.session_state.sayfa = "talep_ekrani"; st.rerun()
        if col2.button("🔍 Sorgulama & Sohbet"): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
        if col3.button("📄 Evrak Rehberi"): st.session_state.sayfa = "evrak_ekrani"; st.rerun()
        if col4.button("🏢 Müdürlükle Konuş"): st.session_state.sayfa = "iletisim_kanali"; st.rerun()

    elif st.session_state.sayfa == "talep_ekrani":
        st.markdown("### 📝 Yeni Şikayet Formu")
        if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
        with st.form("talep"):
            ad = st.text_input("Ad")
            soyad = st.text_input("Soyad")
            ep = st.text_input("E-posta")
            tel = st.text_input("Telefon")
            mud = st.selectbox("Müdürlük", tum_birimler)
            det = st.text_area("Detay")
            if st.form_submit_button("Gönder"):
                if ad and soyad and re.match(EMAIL_PATTERN, ep) and re.match(PHONE_PATTERN, tel):
                    pd.DataFrame([{"ID": str(datetime.now().timestamp())[-6:], "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": ep, "Telefon": tel_temizle(tel), "Müdürlük": mud, "Detay": det, "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                    st.success("Talebiniz Alındı!"); st.balloons()

    elif st.session_state.sayfa == "evrak_ekrani":
        st.markdown("### 📄 Evrak Rehberi")
        if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
        m_s = st.selectbox("Müdürlük", list(EVRAK_DATABANK.keys()))
        i_s = st.selectbox("İşlem", list(EVRAK_DATABANK[m_s].keys()))
        for b in EVRAK_DATABANK[m_s][i_s]: st.write(f"✅ {b}")

    elif st.session_state.sayfa == "sorgu_ekrani":
        st.markdown("### 🔍 Takip & Sohbet")
        if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
        arama = st.text_input("E-posta/Tel")
        sf = st.text_input("Şifre", type="password")
        if arama:
            df_s = veri_yukle()
            if not df_s.empty:
                res = df_s[(df_s["E-posta"] == arama) | (df_s["Telefon"].apply(tel_temizle) == tel_temizle(arama))]
                if not res.empty: st.table(res[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            df_m = mesaj_yukle()
            if not df_m.empty:
                k_msg = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(tel_temizle) == tel_temizle(arama))) & (df_m["Sifre"].astype(str) == str(sf))]
                if not k_msg.empty:
                    b_sec = st.radio("Sohbet:", k_msg["Mudurluk"].unique())
                    for _, r in k_msg[k_msg["Mudurluk"] == b_sec].iterrows():
                        with st.chat_message("user"):
                            st.write(r['Mesaj'])
                            if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi'])), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor":
                            with st.chat_message("assistant"):
                                st.write(r['Cevap'])
                                if r['Mudurluk_Dosya'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("belediye_belgeleri", str(r['Mudurluk_Dosya'])), str(r['Mudurluk_Dosya'])), unsafe_allow_html=True)
                    with st.expander("Yanıtla"):
                        with st.form("rep"):
                            m = st.text_area("Mesaj")
                            f = st.file_uploader("Belge")
                            if st.form_submit_button("Gönder"):
                                fn = "Yok"
                                if f:
                                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                                    fn = f"rep_{datetime.now().strftime('%H%M')}_{f.name}"
                                    with open(os.path.join("yuklenen_belgeler", fn), "wb") as fi: fi.write(f.getbuffer())
                                pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_msg.iloc[0]["Gonderen"], "Telefon": k_msg.iloc[0]["Telefon"], "Sifre": sf, "Mudurluk": b_sec, "Mesaj": m, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                                st.rerun()

    elif st.session_state.sayfa == "iletisim_kanali":
        st.markdown("### 🏢 Müdürlüğe Belge/Mesaj Gönder")
        if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
        with st.form("init"):
            k_mud = st.selectbox("Birim", tum_birimler)
            k_mail = st.text_input("E-posta")
            k_tel = st.text_input("Telefon")
            k_sifre = st.text_input("Şifre")
            k_msg = st.text_area("Mesaj")
            k_file = st.file_uploader("Belge Ekle") # BURASI GERİ GELDİ
            if st.form_submit_button("Gönder"):
                if re.match(EMAIL_PATTERN, k_mail) and re.match(PHONE_PATTERN, k_tel):
                    fn = "Yok"
                    if k_file:
                        if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                        fn = f"init_{datetime.now().strftime('%H%M%S')}_{k_file.name}"
                        with open(os.path.join("yuklenen_belgeler", fn), "wb") as fi: fi.write(k_file.getbuffer())
                    pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Telefon": tel_temizle(k_tel), "Sifre": k_sifre, "Mudurluk": k_mud, "Mesaj": k_msg, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                    st.success("İletildi!")

# --- 🏢 MÜDÜRLÜK ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Sayfaya Dön"):
        st.session_state.portal_modu = "karşılama"
        st.rerun()
    st.markdown("### 🏢 Yönetim Paneli")
    c_a, c_b = st.columns(2)
    adm_b = c_a.selectbox("Biriminiz", tum_birimler)
    adm_s = c_b.text_input("Şifre", type="password")
    if adm_s == "1234":
        t1, t2 = st.tabs(["📋 Şikayetler", "💬 Sohbetler"])
        with t1:
            df_a = veri_yukle()
            if not df_a.empty:
                filt = df_a[df_a["Müdürlük"] == adm_b]
                if not filt.empty:
                    st.dataframe(filt)
                    s_id = st.selectbox("ID Seç", filt["ID"].tolist())
                    c_d, c_y = st.columns(2)
                    y_d = c_d.selectbox("Durum", ["İnceleniyor", "Tamamlandı", "Reddedildi", "Sevk Edildi"])
                    y_sv = c_y.selectbox("Sevk Et", tum_birimler, index=tum_birimler.index(adm_b))
                    if st.button("Güncelle"):
                        idx = df_a[df_a["ID"] == s_id].index
                        df_a.at[idx[0], "Durum"] = y_d if y_sv == adm_b else "Sevk Edildi"
                        df_a.at[idx[0], "Müdürlük"] = y_sv
                        df_a.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                        st.success("Birim güncellendi!"); st.rerun()
        with t2:
            df_m = mesaj_yukle()
            b_m = df_m[df_m["Mudurluk"] == adm_b]
            ara = st.text_input("Ara (E-posta/Tel)")
            v_l = [v for v in b_m["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if v_l:
                v_s = st.selectbox("Seç", v_l)
                v_g = b_m[b_m["Gonderen"] == v_s]
                for _, r in v_g.iterrows():
                    with st.container(border=True):
                        st.write(f"👤 {r['Mesaj']}")
                        if r['Dosya_Adi'] != "Yok": st.markdown(dosya_indirme_linki(os.path.join("yuklenen_belgeler", str(r['Dosya_Adi'])), str(r['Dosya_Adi']), "Vatandaş Belgesi"), unsafe_allow_html=True)
                        if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ {r['Cevap']}")
                with st.form("adm_rep"):
                    ans = st.text_area("Cevap")
                    f_a = st.file_uploader("Belge Gönder")
                    if st.form_submit_button("Yanıtı Gönder"):
                        f_n = "Yok"
                        if f_a:
                            if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                            f_n = f"adm_{datetime.now().strftime('%H%M')}_{f_a.name}"
                            with open(os.path.join("belediye_belgeleri", f_n), "wb") as fi: fi.write(f_a.getbuffer())
                        df_m.at[v_g.index[-1], "Cevap"] = ans
                        df_m.at[v_g.index[-1], "Mudurluk_Dosya"] = f_n
                        df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                        st.rerun()
