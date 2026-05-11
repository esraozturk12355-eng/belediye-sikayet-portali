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

# --- DOSYA İNDİRME FONKSİYONU ---
def dosya_indirme_linki(dosya_verisi, dosya_adi, etiket="İndir"):
    b64 = base64.b64encode(dosya_verisi).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:4px 8px; border-radius:4px; font-size:12px;">📩 {etiket}: {dosya_adi}</a>'

# --- SESSION STATE ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- VERİ YÜKLEME FONKSİYONLARI ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try:
            return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
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

# MÜDÜRLÜKLER VE TÜRLER
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

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Yapay Zeka Destekli Vatandaş Portalı")
st.divider()

# --- 🤖 1. SAYFA: ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("📝 Talep ve Öneri Bildir"): st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Sorgulama & Sohbet"): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("🏢 Müdürlükle İletişim"): st.session_state.sayfa = "iletisim_kanali"; st.rerun()
    if col4.button("📞 İletişim"): st.info("📞 0 (362) 511 44 88")

# --- 📝 2. SAYFA: TALEP FORMU (İstediğin Format) ---
elif st.session_state.sayfa == "talep_ekrani":
    st.markdown("### 📝 Yeni Talep / Şikayet Formu")
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
                st.success(f"✅ Talebiniz Alındı! Takip ID: {sikayet_id}"); st.balloons()
            else:
                st.error("Lütfen formu eksiksiz ve doğru formatta doldurunuz.")

# --- 🔍 3. SAYFA: SORGULAMA VE ÖZEL SOHBET ---
elif st.session_state.sayfa == "sorgu_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    mail_sorgu = st.text_input("E-posta Adresiniz:")
    sifre_sorgu = st.text_input("Sohbet Şifreniz (Varsa):", type="password")
    
    if mail_sorgu:
        df_s = veri_yukle()
        if not df_s.empty:
            res = df_s[df_s["E-posta"] == mail_sorgu]
            if not res.empty: st.markdown("#### 📋 Başvurularınız"), st.table(res[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])

        df_m = mesaj_yukle()
        user_msgs = df_m[(df_m["Gonderen"] == mail_sorgu) & (df_m["Sifre"].astype(str) == str(sifre_sorgu))]
        if not user_msgs.empty:
            birim_list = user_msgs["Mudurluk"].unique().tolist()
            sec_b = st.radio("Hangi müdürlükle olan sohbeti görmek istersiniz?", birim_list, horizontal=True)
            
            st.markdown(f"#### 💬 {sec_b} Sohbet Geçmişi")
            for _, r in user_msgs[user_msgs["Mudurluk"] == sec_b].iterrows():
                with st.chat_message("user"): st.write(f"**Siz:** {r['Mesaj']}")
                if r['Cevap'] != "Bekleniyor":
                    with st.chat_message("assistant"): st.write(f"**Belediye:** {r['Cevap']}")

# --- 🏢 4. SAYFA: İLETİŞİM KANALI ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlük ile İletişim Başlat")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("msg_ilk"):
        k_mud = st.selectbox("Hangi Birim?", tum_birimler)
        k_mail = st.text_input("E-posta:")
        k_sifre = st.text_input("Şifre Belirleyin:", type="password")
        k_msg = st.text_area("Mesajınız:")
        if st.form_submit_button("Gönder"):
            yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_msg, "Dosya_Adi": "Yok", "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}
            pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
            st.success("İletildi!")

# --- 🏢 MÜDÜRLÜK PANELİ ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    adm_b = st.selectbox("Biriminiz:", tum_birimler, key="ab")
    adm_s = st.text_input("Şifre:", type="password", key="as")
    if adm_s == "1234":
        t1, t2 = st.tabs(["Şikayetler", "💬 Sohbetler"])
        with t2:
            df_m = mesaj_yukle()
            birim_m = df_m[df_m["Mudurluk"] == adm_b]
            ara_v = st.text_input("🔍 Vatandaş Ara (E-posta):")
            v_list = [v for v in birim_m["Gonderen"].unique() if ara_v.lower() in str(v).lower()]
            if v_list:
                v_sec = st.selectbox("Kullanıcı Seç:", v_list)
                v_gecmis = birim_m[birim_m["Gonderen"] == v_sec]
                for _, r in v_gecmis.iterrows():
                    st.info(f"👤 Vatandaş: {r['Mesaj']}")
                    if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ Yanıtınız: {r['Cevap']}")
                
                y_not = st.text_area("Cevap Yazın:", key="adm_ans")
                if st.button("Yanıtı Gönder"):
                    df_m.at[v_gecmis.index[-1], "Cevap"] = y_not
                    df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                    st.success("İletildi!"); st.rerun()
