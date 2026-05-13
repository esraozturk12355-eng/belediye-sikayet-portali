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

# --- 📚 TAM KAPSAMLI EVRAK VERİTABANI (10 MÜDÜRLÜK - HER BİRİNDE 5 İŞLEM) ---
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
        "Nikah Başvurusu": ["Sağlık Raporu", "4 Adet Fotoğraf", "Kimlik Aslı", "Nüfus Kayıt Örneği", "Bekarlık Belgesi (Yabancılar için)"],
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
        "Atık Yağ Toplama Talebi": ["Adres Bilgisi", "Atık Miktarı", "İletişim", "Dilekçe", "Firma Bilgisi (İşyerleri için)"],
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

tum_birimler = sorted([f"{k}" for k in EVRAK_DATABANK.keys()])

# --- DOSYA İNDİRME FONKSİYONU ---
def dosya_indirme_linki(dosya_verisi, dosya_adi, etiket="İndir"):
    b64 = base64.b64encode(dosya_verisi).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:4px 8px; border-radius:4px; font-size:12px;">📩 {etiket}: {dosya_adi}</a>'

# --- SESSION STATE ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, encoding="utf-8-sig")
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
    return tel[1:] if tel.startswith("0") else tel

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
    if col4.button("🏢 Müdürlükle İletişim"): st.session_state.sayfa = "iletisim_kanali"; st.rerun()

# --- 📝 2. SAYFA: TALEP FORMU ---
elif st.session_state.sayfa == "talep_ekrani":
    st.markdown("### 📝 Yeni Talep / Şikayet Formu")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız")
            eposta = st.text_input("E-posta Adresiniz")
            is_valid = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', eposta)) if eposta else False
        with c2:
            soyad = st.text_input("Soyadınız")
            tel = st.text_input("Telefon Numaranız")
        sec_mud = st.selectbox("İlgili Müdürlük", tum_birimler)
        detay = st.text_area("Açıklama")
        if st.button("Kaydet ve Gönder"):
            if ad and soyad and is_valid:
                sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni = {"ID": sid, "Sıra_No": 1, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": tel_temizle(tel), "Müdürlük": sec_mud, "Detay": detay.replace(","," "), "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
                pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"Talebiniz Alındı! Takip ID: {sid}"); st.balloons()

# --- 📄 3. SAYFA: EVRAK REHBERİ ---
elif st.session_state.sayfa == "evrak_ekrani":
    st.markdown("### 📄 Gerekli Evraklar Rehberi")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    m_sec = st.selectbox("Müdürlük Seçiniz:", ["Seçiniz..."] + list(EVRAK_DATABANK.keys()))
    if m_sec != "Seçiniz...":
        i_sec = st.selectbox("İşlem Seçiniz:", list(EVRAK_DATABANK[m_sec].keys()))
        if i_sec:
            st.info(f"📋 **{i_sec}** için istenen belgeler:")
            for b in EVRAK_DATABANK[m_sec][i_sec]: st.write(f"✅ {b}")

# --- 🔍 4. SAYFA: SORGULAMA ---
elif st.session_state.sayfa == "sorgu_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    m_sorgu = st.text_input("E-posta Adresiniz:")
    s_sorgu = st.text_input("Mesaj Şifreniz:", type="password")
    if m_sorgu:
        df_s = veri_yukle()
        if not df_s.empty:
            res = df_s[df_s["E-posta"] == m_sorgu]
            if not res.empty: st.markdown("#### 📋 Şikayet Durumlarınız"), st.table(res[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
        df_m = mesaj_yukle()
        k_msgs = df_m[(df_m["Gonderen"] == m_sorgu) & (df_m["Sifre"].astype(str) == str(s_sorgu))]
        if not k_msgs.empty:
            b_list = k_msgs["Mudurluk"].unique().tolist()
            sec_b = st.radio("Sohbeti Seç:", b_list, horizontal=True)
            for _, r in k_msgs[k_msgs["Mudurluk"] == sec_b].iterrows():
                with st.chat_message("user"): st.write(r['Mesaj'])
                if r['Cevap'] != "Bekleniyor":
                    with st.chat_message("assistant"): st.write(r['Cevap'])

# --- 🏢 5. SAYFA: İLETİŞİM ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlüğe Belge / Mesaj Gönder")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("msg_form"):
        k_mud = st.selectbox("Birim:", tum_birimler)
        k_mail = st.text_input("E-posta:")
        k_sifre = st.text_input("Şifre Belirleyin:", type="password")
        k_msg = st.text_area("Mesajınız:")
        k_file = st.file_uploader("Dosya Ekle:")
        if st.form_submit_button("Gönder"):
            fn = "Yok"
            if k_file:
                if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                fn = f"{datetime.now().strftime('%H%M%S')}_{k_file.name}"
                with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(k_file.getbuffer())
            yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_msg, "Dosya_Adi": fn, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}
            pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
            st.success("İletildi!")

# --- 🏢 MÜDÜRLÜK PANELİ (ADMIN) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    adm_b = st.selectbox("Biriminiz:", tum_birimler, key="adm_birim")
    adm_s = st.text_input("Şifre:", type="password", key="adm_pass")
    if adm_s == "1234":
        df_m = mesaj_yukle()
        birim_m = df_m[df_m["Mudurluk"] == adm_b]
        ara_v = st.text_input("🔍 Vatandaş E-posta ile Ara:")
        v_list = [v for v in birim_m["Gonderen"].unique() if ara_v.lower() in str(v).lower()]
        if v_list:
            v_sec = st.selectbox("Kullanıcı Seç:", v_list)
            v_gecmis = birim_m[birim_m["Gonderen"] == v_sec]
            for idx, r in v_gecmis.iterrows():
                st.info(f"👤 Vatandaş: {r['Mesaj']}")
                if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ Yanıtınız: {r['Cevap']}")
            y_not = st.text_area("Cevap Yazın:", key="ans_adm")
            if st.button("Yanıtı Gönder"):
                df_m.at[v_gecmis.index[-1], "Cevap"] = y_not
                df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                st.success("İletildi!"); st.rerun()
