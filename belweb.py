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

# --- ASİSTAN BİLGİ BANKASI ---
BELEDİYE_BİLGİLERİ = {
    "konum": "Pazar Mah. Atatürk Bulvarı No:165, Ondokuzmayıs/SAMSUN",
    "telefon": "0 (362) 511 44 88",
    "saat": "Hafta içi 08:30 - 17:30",
    "web": "www.19mayis.bel.tr",
    "evrak": {
        "İmar": "Tapu, Mimari Proje, İmar Durum Belgesi.",
        "Yazı İşleri": "Kimlik Fotokopisi, Islak İmzalı Dilekçe.",
        "Nikah": "Sağlık Raporu, 4 Fotoğraf, Nüfus Kayıt Örneği."
    }
}

# --- SESSION STATE (Sayfa ve Mesaj Yönetimi) ---
if "sayfa" not in st.session_state:
    st.session_state.sayfa = "asistan"
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- ÜST BAŞLIK VE LOGO ALANI ---
c1, c2 = st.columns([1, 6]) 
with c1:
    logo_dosyasi = "logo.jfif"
    if os.path.exists(logo_dosyasi):
        st.image(logo_dosyasi, width=120)
    else:
        st.write("# 🏛️") 

with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Akıllı Vatandaş Çözüm Merkezi")

st.divider()

# --- VERİ YÜKLEME FONKSİYONU ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

# TELEFON TEMİZLEME
def tel_temizle(tel):
    tel = str(tel).strip()
    if tel.startswith("0"): return tel[1:]
    return tel

# MÜDÜRLÜKLER
sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + [
    "Emlak ve İstimlak Müdürlüğü", "İklim Değişikliği ve Sıfır Atık Müdürlüğü", 
    "Destek Hizmetleri Müdürlüğü", "Yapı Kontrol Müdürlüğü"
])))

# --- 🤖 BÖLÜM 1: AI ASİSTAN (BUTONLU VE KONUŞKAN) ---
if st.session_state.sayfa == "asistan":
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Ondokuzmayıs Belediyesi Akıllı Asistanına hoş geldiniz. 😊 Size nasıl yardımcı olabilirim?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("### Hızlı İşlemler")
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    if row1_col1.button("📝 Şikayet Oluşturmak İstiyorum"):
        st.session_state.messages.append({"role": "assistant", "content": "Anlaşıldı, sizi hemen yeni şikayet oluşturma sayfasına yönlendiriyorum..."})
        st.session_state.sayfa = "portal"
        st.rerun()

    if row1_col2.button("🔍 Şikayetlerimi Görüntülemek İstiyorum"):
        st.session_state.messages.append({"role": "assistant", "content": "Tamamdır, şikayet sorgulama ekranına sizi yönlendiriyorum..."})
        st.session_state.sayfa = "portal"
        st.rerun()

    if row2_col1.button("📄 Evrak Bilgisi Almak İstiyorum"):
        ans = "Gerekli evrak bilgilerini hazırladım: \n" + "\n".join([f"- **{k}**: {v}" for k, v in BELEDİYE_BİLGİLERİ['evrak'].items()])
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.rerun()

    if row2_col2.button("📞 Belediye İletişim & Konum"):
        ans = f"📞 **Telefon:** {BELEDİYE_BİLGİLERİ['telefon']} \n📍 **Adres:** {BELEDİYE_BİLGİLERİ['konum']} \n⏰ **Çalışma Saatleri:** {BELEDİYE_BİLGİLERİ['saat']}"
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.rerun()

    if prompt := st.chat_input("Veya buraya yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        p_low = prompt.lower()
        
        if any(x in p_low for x in ["şikayet", "sikayet", "oluştur"]):
            st.session_state.messages.append({"role": "assistant", "content": "Tabii ki, şikayet formuna sizi yönlendiriyorum..."})
            st.session_state.sayfa = "portal"
            st.rerun()
        elif any(x in p_low for x in ["sorgu", "takip", "bakmak"]):
            st.session_state.messages.append({"role": "assistant", "content": "Şikayet sorgulama sayfasına yönlendiriliyorsunuz..."})
            st.session_state.sayfa = "portal"
            st.rerun()
        elif any(x in p_low for x in ["konum", "nerede", "adres"]):
            st.session_state.messages.append({"role": "assistant", "content": f"Belediyemiz şu adrestedir: {BELEDİYE_BİLGİLERİ['konum']}"})
            st.rerun()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Size yardımcı olabilmem için yukarıdaki butonları kullanabilir veya 'Şikayet oluştur' gibi net komutlar yazabilirsiniz."})
            st.rerun()

# --- 📝 BÖLÜM 2: ANA PORTAL (ORİJİNAL KODUN) ---
elif st.session_state.sayfa == "portal":
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"
        st.rerun()

    tab1, tab2 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle"])

    # --- TAB 1: YENİ ŞİKAYET ---
    with tab1:
        st.markdown("### 📝 Yeni Şikayet Formu")
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
                else:
                    st.warning("⚠️ Lütfen geçerli bir e-posta adresi giriniz!")

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
            else:
                st.error("Lütfen formu eksiksiz ve doğru formatta doldurunuz.")

    # --- TAB 2: SORGULAMA ---
    with tab2:
        st.markdown("### 🔍 Şikayet Sorgulama")
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
                else:
                    st.warning("⚠️ Bu bilgilere ait bir şikayet kaydı bulunamadı.")

# --- MÜDÜRLÜK PANELİ ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili Girişi)"):
    cp1, cp2 = st.columns(2)
    with cp1:
        admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
    with cp2:
        sifre = st.text_input("Şifre:", type="password", key="adm_pass")
    if sifre == "1234":
        df_admin = veri_yukle()
        # ... (Geri kalan admin paneli kodun buraya gelir)
       
