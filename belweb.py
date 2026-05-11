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

# --- 📚 EVRAK REHBERİ ---
EVRAK_REHBERI = {
    "İmar ve Şehircilik Müdürlüğü": {"İnşaat Ruhsatı": ["Tapu", "Proje"], "İskan": ["Enerji Kimliği", "SGK"]},
    "Yazı İşleri Müdürlüğü": {"Nikah": ["Sağlık Raporu", "Fotoğraf"]},
    "Zabıta Müdürlüğü": {"Ruhsat": ["Kira Kontratı", "Vergi Levhası"]}
}

# --- SESSION STATE ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', encoding="utf-8-sig")
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

tum_birimler = ["Destek Hizmetleri", "Emlak ve İstimlak", "Fen İşleri", "Mali Hizmetler", "Veteriner İşleri", "Yapı Kontrol", "Yazı İşleri", "Zabıta", "İklim Değişikliği ve Sıfır Atık", "İmar ve Şehircilik"]

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Birim Bazlı Vatandaş İletişim Portalı")
st.divider()

# --- 🤖 1. SAYFA: ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    col1, col2, col3, col4, col5 = st.columns(5)
    if col1.button("📝 Talep/Öneri Bildir"): st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Sorgulama & Sohbet"): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("📄 Evrak Bilgisi"): st.session_state.sayfa = "evrak_ekrani"; st.rerun()
    if col4.button("🏢 Müdürlükle Konuş"): st.session_state.sayfa = "iletisim_kanali"; st.rerun()
    if col5.button("📞 İletişim"): st.info("📞 0 (362) 511 44 88")

# --- 📝 2. SAYFA: TALEP FORMU ---
elif st.session_state.sayfa == "talep_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("talep"):
        ad, soyad = st.columns(2)
        v_ad, v_soyad = ad.text_input("Ad"), soyad.text_input("Soyad")
        v_mail = st.text_input("E-posta")
        v_mud = st.selectbox("Müdürlük", tum_birimler)
        v_detay = st.text_area("Açıklama")
        if st.form_submit_button("Kaydet"):
            sid = str(datetime.now().timestamp()).replace(".","")[-6:]
            yeni = {"ID": sid, "Sıra_No": 1, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": v_ad, "Soyad": v_soyad, "E-posta": v_mail, "Telefon": "Belirtilmedi", "Müdürlük": v_mud, "Detay": v_detay.replace(","," "), "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
            pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            st.success(f"Talebiniz Alındı! ID: {sid}")

# --- 🔍 3. SAYFA: SORGULAMA VE ÖZEL SOHBET ---
elif st.session_state.sayfa == "sorgu_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    mail_sorgu = st.text_input("E-posta Adresiniz:")
    sifre_sorgu = st.text_input("Mesaj Şifreniz:", type="password")
    
    if mail_sorgu and sifre_sorgu:
        df_m = mesaj_yukle()
        kullanici_mesajlari = df_m[(df_m["Gonderen"] == mail_sorgu) & (df_m["Sifre"].astype(str) == str(sifre_sorgu))]
        
        if not kullanici_mesajlari.empty:
            # --- BİRİM SEÇİCİ (Kullanıcının mesajlaştığı birimler) ---
            aktif_birimler = kullanici_mesajlari["Mudurluk"].unique().tolist()
            secilen_birim = st.radio("Hangi birimle olan görüşmenizi görmek istersiniz?", aktif_birimler, horizontal=True)
            
            st.write("---")
            st.markdown(f"#### 💬 {secilen_birim} ile Sohbet Geçmişi")
            birim_gecmisi = kullanici_mesajlari[kullanici_mesajlari["Mudurluk"] == secilen_birim]
            
            for idx, row in birim_gecmisi.iterrows():
                with st.chat_message("user"):
                    st.write(f"**Siz ({row['Tarih']}):** {row['Mesaj']}")
                    if row['Dosya_Adi'] != "Yok": st.write(f"📎 Dosyanız: {row['Dosya_Adi']}")
                if row['Cevap'] != "Bekleniyor":
                    with st.chat_message("assistant"):
                        st.write(f"**{row['Mudurluk']} ({row['Tarih']}):** {row['Cevap']}")
                        if row['Mudurluk_Dosya'] != "Yok":
                            yol = os.path.join("belediye_belgeleri", str(row['Mudurluk_Dosya']))
                            if os.path.exists(yol):
                                with open(yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(row['Mudurluk_Dosya']), "Birim Belgesi"), unsafe_allow_html=True)
            
            with st.expander(f"{secilen_birim} Birimine Yeni Mesaj Yaz"):
                with st.form(f"cevap_form_{secilen_birim}"):
                    yeni_msg = st.text_area("Mesajınız:")
                    yeni_file = st.file_uploader("Dosya Ekle (Opsiyonel):")
                    if st.form_submit_button("Gönder"):
                        d_adi = "Yok"
                        if yeni_file:
                            if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                            d_adi = f"ek_{datetime.now().strftime('%H%M')}_{yeni_file.name}"
                            with open(os.path.join("yuklenen_belgeler", d_adi), "wb") as f: f.write(yeni_file.getbuffer())
                        yeni_row = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": mail_sorgu, "Sifre": str(sifre_sorgu), "Mudurluk": secilen_birim, "Mesaj": yeni_msg, "Dosya_Adi": d_adi, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}
                        pd.DataFrame([yeni_row]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                        st.success("İletildi!"); st.rerun()
        else: st.warning("Bu bilgilerle eşleşen bir sohbet kaydı bulunamadı.")

# --- 📄 4. SAYFA: EVRAK ---
elif st.session_state.sayfa == "evrak_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    m_sec = st.selectbox("Müdürlük:", list(EVRAK_REHBERI.keys()))
    i_sec = st.selectbox("İşlem:", list(EVRAK_REHBERI[m_sec].keys()))
    for b in EVRAK_REHBERI[m_sec][i_sec]: st.write(f"✅ {b}")

# --- 🏢 5. SAYFA: İLETİŞİM KANALI ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlük ile İletişim Başlat")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("ilk_msg"):
        k_mud = st.selectbox("Hangi Müdürlük?", tum_birimler)
        k_mail = st.text_input("E-postanız:")
        k_sifre = st.text_input("Sorgulama Şifresi Belirleyin:", type="password")
        k_msg = st.text_area("Mesajınız:")
        k_file = st.file_uploader("Belge Seçin:")
        if st.form_submit_button("Gönder"):
            d_adi = "Yok"
            if k_file:
                if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                d_adi = f"{datetime.now().strftime('%H%M%S')}_{k_file.name}"
                with open(os.path.join("yuklenen_belgeler", d_adi), "wb") as f: f.write(k_file.getbuffer())
            yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_msg, "Dosya_Adi": d_adi, "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}
            pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
            st.success("Mesaj iletildi!")

# --- 🏢 MÜDÜRLÜK PANELİ ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    adm_b = st.selectbox("Biriminiz:", tum_birimler, key="ab")
    adm_s = st.text_input("Şifre:", type="password", key="as")
    if adm_s == "1234":
        df_m = mesaj_yukle()
        birim_m = df_m[df_m["Mudurluk"] == adm_b]
        arama_v = st.text_input("🔍 Vatandaş E-posta ile Ara:", placeholder="ornek@mail.com")
        
        if arama_v:
            v_gecmis = birim_m[birim_m["Gonderen"] == arama_v]
            if not v_gecmis.empty:
                st.markdown(f"### 💬 {arama_v} ile Konuşma")
                for i, row in v_gecmis.iterrows():
                    with st.container(border=True):
                        st.write(f"📅 **{row['Tarih']}** | 👤 Vatandaş: {row['Mesaj']}")
                        if row['Dosya_Adi'] != "Yok":
                            yol = os.path.join("yuklenen_belgeler", str(row['Dosya_Adi']))
                            if os.path.exists(yol):
                                with open(yol, "rb") as f: st.markdown(dosya_indirme_linki(f.read(), str(row['Dosya_Adi']), "Vatandaş Belgesi"), unsafe_allow_html=True)
                        if row['Cevap'] != "Bekleniyor": st.success(f"🏛️ Yanıtınız: {row['Cevap']}")
                
                son_id = v_gecmis.index[-1]
                y_not = st.text_area("Yanıtınız:", key="adm_yanit")
                y_file = st.file_uploader("Belge Gönder:", key="adm_file")
                if st.button("Yanıtı Gönder"):
                    m_d_adi = "Yok"
                    if y_file:
                        if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                        m_d_adi = f"belediye_{son_id}_{y_file.name}"
                        with open(os.path.join("belediye_belgeleri", m_d_adi), "wb") as f: f.write(y_file.getbuffer())
                    df_m.at[son_id, "Cevap"] = y_not
                    df_m.at[son_id, "Mudurluk_Dosya"] = m_d_adi
                    df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                    st.success("İletildi!"); st.rerun()
        else:
            st.write("Gelen Mesajlar (Özet):")
            st.dataframe(birim_m[["Tarih", "Gonderen", "Mesaj"]].tail(5))
