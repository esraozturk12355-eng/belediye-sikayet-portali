import streamlit as st
import pandas as pd
import os
import re
import base64
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Şikayet Portalı", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- DOSYA İNDİRME FONKSİYONU ---
def dosya_indirme_linki(dosya_verisi, dosya_adi):
    b64 = base64.b64encode(dosya_verisi).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:8px 16px; border-radius:4px;">📩 {dosya_adi} İndir</a>'

# --- 📚 EVRAK REHBERİ VERİSİ ---
EVRAK_REHBERI = {
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı": ["Tapu Kaydı", "Mimari Proje", "İmar Durum Belgesi"],
        "Yapı Kullanma İzin Belgesi (İskan)": ["Enerji Kimlik Belgesi", "SGK İlişiksiz Belgesi"]
    },
    "Yazı İşleri Müdürlüğü": {
        "Nikah Başvurusu": ["Sağlık Raporu", "4 Adet Fotoğraf", "Nüfus Kayıt Örneği"],
        "Encümen Kararı": ["Dilekçe", "Karar Tarih/Sayı Bilgisi"]
    },
    "Zabıta Müdürlüğü": {
        "İşyeri Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "Oda Kaydı"]
    }
}

# --- SESSION STATE (SAYFA YÖNETİMİ) ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"
if "messages" not in st.session_state: st.session_state.messages = []

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap"]
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

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
with c1:
    if os.path.exists("logo.jfif"): st.image("logo.jfif", width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Yapay Zeka Destekli Vatandaş Portalı")

st.divider()

# --- 🤖 BÖLÜM 1: AKILLI ASİSTAN (ANA EKRAN) ---
if st.session_state.sayfa == "asistan":
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Ben Akıllı Asistanınız. 😊 Size bugün nasıl yardımcı olabilirim? Aşağıdaki butonları kullanarak işleminize hemen başlayabilirsiniz."})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("### 🚀 Hızlı İşlemler")
    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
    
    if c_btn1.button("📝 Şikayet Oluştur"):
        st.session_state.sayfa = "yeni_sikayet"; st.rerun()
    if c_btn2.button("🔍 Sorgulama Yap"):
        st.session_state.sayfa = "sorgulama"; st.rerun()
    if c_btn3.button("📄 Evrak Rehberi"):
        st.session_state.sayfa = "evrak_rehberi"; st.rerun()
    if c_btn4.button("🏢 Belge/Mesaj Gönder"):
        st.session_state.sayfa = "mesaj_gonder"; st.rerun()

    if prompt := st.chat_input("Veya buraya yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        p_low = prompt.lower()
        if any(x in p_low for x in ["şikayet", "sikayet"]): st.session_state.sayfa = "yeni_sikayet"; st.rerun()
        elif "sorgu" in p_low: st.session_state.sayfa = "sorgulama"; st.rerun()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Size yardımcı olabilmem için lütfen hızlı işlem butonlarını kullanın."})
            st.rerun()

# --- 📝 BÖLÜM 2: YENİ ŞİKAYET OLUŞTUR ---
elif st.session_state.sayfa == "yeni_sikayet":
    st.markdown("### 📝 Yeni Şikayet Formu")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız")
            eposta = st.text_input("E-posta Adresiniz")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = bool(re.match(email_pattern, eposta, re.IGNORECASE)) if eposta else False
        with c2:
            soyad = st.text_input("Soyadınız")
            tel_input = st.text_input("Telefon Numaranız")
        
        mud_sec = st.selectbox("İlgili Müdürlük", tum_birimler)
        detay = st.text_area("Şikayet Detayı")
        
        if st.button("Şikayeti Kaydet"):
            if ad and soyad and is_email_valid and tel_input:
                sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                kayit = {"ID": sid, "Sıra_No": 1, "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": tel_temizle(tel_input), "Müdürlük": mud_sec, "Detay": detay.replace(","," "), "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
                pd.DataFrame([kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"Şikayet alındı! ID: {sid}"); st.balloons()
            else: st.error("Lütfen formu eksiksiz doldurun.")

# --- 🔍 BÖLÜM 3: SORGULAMA ---
elif st.session_state.sayfa == "sorgulama":
    st.markdown("### 🔍 Şikayet ve Mesaj Sorgulama")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    mail_sorgu = st.text_input("E-posta veya Telefon numaranız:")
    sifre_sorgu = st.text_input("Mesaj Şifreniz (Varsa):", type="password")
    
    if mail_sorgu:
        df_s = veri_yukle()
        if not df_s.empty:
            st.write("Şikayet Kayıtlarınız:")
            st.table(df_s[df_s["E-posta"] == mail_sorgu])
        
        df_m = mesaj_yukle()
        if not df_m.empty:
            kendi = df_m[(df_m["Gonderen"] == mail_sorgu) & (df_m["Sifre"].astype(str) == str(sifre_sorgu))]
            if not kendi.empty:
                st.write("Mesaj Yanıtlarınız:")
                st.dataframe(kendi[["Tarih", "Mudurluk", "Mesaj", "Cevap"]])

# --- 📄 BÖLÜM 4: EVRAK REHBERİ ---
elif st.session_state.sayfa == "evrak_rehberi":
    st.markdown("### 📄 Müdürlük Evrak Rehberi")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    m_s = st.selectbox("Müdürlük Seçin:", ["Seçiniz..."] + sorted(list(EVRAK_REHBERI.keys())))
    if m_s != "Seçiniz...":
        i_s = st.selectbox("İşlem Seçin:", list(EVRAK_REHBERI[m_s].keys()))
        st.info(f"**{i_s}** için gerekli belgeler:")
        for b in EVRAK_REHBERI[m_s][i_s]: st.write(f"✅ {b}")

# --- 🏢 BÖLÜM 5: MESAJ / BELGE GÖNDER ---
elif st.session_state.sayfa == "mesaj_gonder":
    st.markdown("### 🏢 Müdürlüğe Belge/Mesaj Gönder")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.form("msg_form"):
        k_mud = st.selectbox("Müdürlük:", tum_birimler)
        k_mail = st.text_input("E-posta:")
        k_sifre = st.text_input("Şifre Belirleyin:", type="password")
        k_msg = st.text_area("Mesajınız:")
        k_file = st.file_uploader("Dosya Seçin:")
        if st.form_submit_button("Gönder"):
            if k_mail and k_sifre and k_msg:
                d_adi = "Yok"
                if k_file:
                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                    d_adi = f"{datetime.now().strftime('%H%M%S')}_{k_file.name}"
                    with open(os.path.join("yuklenen_belgeler", d_adi), "wb") as f: f.write(k_file.getbuffer())
                
                yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_msg.replace(",","."), "Dosya_Adi": d_adi, "Cevap": "Bekleniyor"}
                pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                st.success("İletildi!")

# --- 🏢 BÖLÜM 6: MÜDÜRLÜK PANELİ (ADMIN) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    adm_b = st.selectbox("Birim:", tum_birimler, key="adm_birim")
    adm_s = st.text_input("Şifre:", type="password", key="adm_pass")
    
    if adm_s == "1234":
        t1, t2 = st.tabs(["📋 Şikayet Yönetimi", "💬 Mesajlar & Belgeler"])
        with t1:
            df_a = veri_yukle()
            if not df_a.empty:
                filtre = df_a[df_a["Müdürlük"] == adm_b]
                st.dataframe(filtre)
        with t2:
            df_m = mesaj_yukle()
            if not df_m.empty:
                birim_msj = df_m[df_m["Mudurluk"] == adm_b]
                for i, row in birim_msj.iterrows():
                    with st.container(border=True):
                        st.write(f"📧 {row['Gonderen']} | 💬 {row['Mesaj']}")
                        if row['Dosya_Adi'] != "Yok":
                            yol = os.path.join("yuklenen_belgeler", str(row['Dosya_Adi']))
                            if os.path.exists(yol):
                                with open(yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(row['Dosya_Adi'])), unsafe_allow_html=True)
                        y_not = st.text_area("Yanıt:", key=f"y_{i}")
                        if st.button("Gönder", key=f"b_{i}"):
                            df_m.at[i, "Cevap"] = y_not
                            df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                            st.success("Yanıtlandı!"); st.rerun()
