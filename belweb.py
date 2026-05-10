import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Şikayet Portalı", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- BİLGİ BANKASI ---
BELEDİYE_BİLGİLERİ = {
    "konum": "Pazar Mah. Atatürk Bulvarı No:165, Ondokuzmayıs/SAMSUN",
    "telefon": "0 (362) 511 44 88",
    "çalışma_saatleri": "Hafta içi 08:30 - 17:30",
}

sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}

# --- SESSION STATE (Sayfa Yönetimi) ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"
if "messages" not in st.session_state: st.session_state.messages = []

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def tel_temizle(tel):
    tel = str(tel).strip()
    if tel.startswith("0"): return tel[1:]
    return tel

# --- ÜST BAŞLIK VE LOGO ---
c1, c2 = st.columns([1, 6]) 
with c1:
    if os.path.exists("logo.jfif"): st.image("logo.jfif", width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Akıllı Vatandaş Portalı")

st.divider()

# --- 🤖 1. BÖLÜM: BİLGE ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Belediye Asistanı")
    
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Ben Ondokuzmayıs Belediyesi asistanıyım. Size konum, telefon bilgisi verebilir veya şikayet süreçlerine yönlendirebilirim."})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Hızlı Seçenekler
    st.write("---")
    col1, col2, col3 = st.columns(3)
    if col1.button("📝 Yeni Şikayet Oluştur"): st.session_state.sayfa = "sikayet_olustur"; st.rerun()
    if col2.button("🔍 Şikayet Sorgula"): st.session_state.sayfa = "sorgulama"; st.rerun()
    if col3.button("📄 Gerekli Evraklar"): st.write("Evrak listesi çok yakında burada olacak!"); # Geliştirilebilir

    if prompt := st.chat_input("Belediye nerede? / Şikayet etmek istiyorum..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        p_low = prompt.lower()
        
        if any(x in p_low for x in ["konum", "nerede", "adres"]):
            ans = f"📍 Belediyemiz: {BELEDİYE_BİLGİLERİ['konum']}"
        elif any(x in p_low for x in ["telefon", "numara", "iletişim"]):
            ans = f"📞 İletişim: {BELEDİYE_BİLGİLERİ['telefon']}"
        elif "şikayet" in p_low or "sikayet" in p_low:
            ans = "Sizi şikayet formuna yönlendiriyorum..."
            st.session_state.sayfa = "sikayet_olustur"; st.rerun()
        else:
            ans = "Üzgünüm, bunu tam anlayamadım. Şikayet oluşturmak veya sorgulamak için butonları kullanabilirsiniz."
        
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.rerun()

# --- 📝 2. BÖLÜM: YENİ ŞİKAYET FORMU (TAM HALİ) ---
elif st.session_state.sayfa == "sikayet_olustur":
    st.header("📝 Yeni Şikayet Formu")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız", key="f_ad")
            eposta = st.text_input("E-posta Adresiniz", key="f_mail")
            # --- E-POSTA KONTROLÜ ---
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = False
            if eposta != "": 
                if re.match(email_pattern, eposta, re.IGNORECASE):
                    st.success("E-posta formatı geçerli. ✅")
                    is_email_valid = True
                else: st.warning("⚠️ Lütfen geçerli bir e-posta uzantısı giriniz.")

        with c2:
            soyad = st.text_input("Soyadınız", key="f_soyad")
            tel_input = st.text_input("Telefon Numaranız", key="f_tel")

        # --- MÜDÜRLÜK VE ÖNERİLER ---
        tum_birimler = sorted(list(sikayet_turleri_dict.keys()))
        secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler)
        tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel", "Diğer"])
        sikayet_turu = st.selectbox("Şikayet Türü (Öneriler)", tur_listesi)
        detay = st.text_area("Şikayet Detayı")

        if st.button("Şikayeti Kaydet"):
            if ad and soyad and is_email_valid and tel_input and detay:
                temiz_tel = tel_temizle(tel_input)
                df_mevcut = veri_yukle()
                yeni_sira_no = 1
                if not df_mevcut.empty:
                    birim_kayitlari = df_mevcut[df_mevcut["Müdürlük"] == secilen_mudurluk]
                    if not birim_kayitlari.empty:
                        yeni_sira_no = int(birim_kayitlari["Sıra_No"].max()) + 1
                
                sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni_kayit = {
                    "ID": sikayet_id, "Sıra_No": yeni_sira_no, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": temiz_tel,
                    "Müdürlük": secilen_mudurluk, "Tür": sikayet_turu, "Detay": detay, "Durum": "İnceleniyor"
                }
                pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"✅ Şikayetiniz başarıyla alındı! Takip No: {sikayet_id}")
                st.balloons()
            else: st.error("Lütfen tüm alanları doğru şekilde doldurunuz!")

# --- 🔍 3. BÖLÜM: SORGULAMA ---
elif st.session_state.sayfa == "sorgulama":
    st.header("🔍 Şikayet Sorgulama")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
    if arama:
        temiz_arama = tel_temizle(arama)
        df = veri_yukle()
        if not df.empty:
            df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
            sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == temiz_arama)]
            if not sonuclar.empty:
                st.table(sonuclar[["Tarih", "Müdürlük", "Durum"]])
            else: st.warning("Kayıt bulunamadı.")

# --- 🏢 4. BÖLÜM: MÜDÜRLÜK PANELİ (ŞİFRELİ) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    sifre = st.text_input("Giriş Şifresi", type="password")
    if sifre == "1234":
        df_admin = veri_yukle()
        if not df_admin.empty:
            admin_birim = st.selectbox("Biriminiz:", sorted(list(sikayet_turleri_dict.keys())))
            filtreli = df_admin[df_admin["Müdürlük"] == admin_birim]
            st.dataframe(filtreli)
            # Buraya güncelleme kodlarını (Daha önceki onayla butonunu) ekleyebilirsin.
    elif sifre != "": st.error("Hatalı Şifre!")
