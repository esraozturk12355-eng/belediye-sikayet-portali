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

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Telefon", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap", "Mudurluk_Dosya"]
    if os.path.exists("mesajlar.csv"):
        try: return pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def tel_temizle(tel):
    tel = str(tel).strip()
    if tel.startswith("0"): return tel[1:]
    return tel

def dosya_indirme_linki(dosya_yolu, dosya_adi, etiket="İndir"):
    if not os.path.exists(dosya_yolu): return "⚠️ Dosya Yok"
    with open(dosya_yolu, "rb") as f: data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:4px 8px; border-radius:4px; font-size:12px;">📩 {etiket}: {dosya_adi}</a>'

# --- VERİ VE SABİTLER ---
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

# --- SESSION STATE ---
if "portal_modu" not in st.session_state: st.session_state.portal_modu = "karşılama"
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan_ana"

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Dijital Vatandaş & Yönetim Portalı")
st.divider()

# --- 🚀 1. EKRAN: GİRİŞ SEÇİMİ ---
if st.session_state.portal_modu == "karşılama":
    st.markdown("<h2 style='text-align: center;'>Hoş Geldiniz! Lütfen Giriş Türünü Seçiniz</h2>", unsafe_allow_html=True)
    st.write("---")
    cv, cm = st.columns(2)
    with cv:
        st.info("### 👤 Vatandaş Portalı\nTalep oluşturma ve hızlı işlemler için giriş yapın.")
        if st.button("Vatandaş Girişi", use_container_width=True):
            st.session_state.portal_modu = "vatandas"
            st.rerun()
    with cm:
        st.success("### 🏢 Müdürlük Paneli\nYetkili girişi yaparak talepleri yönetin.")
        if st.button("Müdürlük Girişi", use_container_width=True, type="primary"):
            st.session_state.portal_modu = "mudurluk"
            st.rerun()

# --- 👤 2. EKRAN: VATANDAŞ PORTALI (ASİSTAN & HIZLI İŞLEMLER) ---
elif st.session_state.portal_modu == "vatandas":
    if st.sidebar.button("🏠 Ana Ekrana Dön"): 
        st.session_state.portal_modu = "karşılama"
        st.session_state.sayfa = "asistan_ana"
        st.rerun()
    
    # --- ASİSTAN ANA EKRAN (HIZLI İŞLEMLER) ---
    if st.session_state.sayfa == "asistan_ana":
        st.markdown("### 🤖 Akıllı Asistan: Size Nasıl Yardımcı Olabilirim?")
        st.write("Hızlı işlem yapmak için aşağıdaki butonları kullanabilirsiniz:")
        
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📝 Yeni Talep Oluştur", use_container_width=True): 
            st.session_state.sayfa = "talep_yeni"; st.rerun()
        if c2.button("🔍 Talep Sorgula", use_container_width=True): 
            st.session_state.sayfa = "talep_sorgu"; st.rerun()
        if c3.button("💬 Müdürlükle Konuş", use_container_width=True): 
            st.session_state.sayfa = "mudurluk_sohbet"; st.rerun()
        if c4.button("📄 Evrak Rehberi", use_container_width=True): 
            st.session_state.sayfa = "evrak_rehberi"; st.rerun()

    # --- HIZLI İŞLEM: TALEP OLUŞTUR ---
    elif st.session_state.sayfa == "talep_yeni":
        st.markdown("### 📝 Yeni Talep Oluştur")
        if st.button("⬅️ Asistan Ana Menü"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                ad = st.text_input("Adınız")
                eposta = st.text_input("E-posta Adresiniz")
                email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
                is_email_valid = bool(re.match(email_pattern, eposta, re.IGNORECASE)) if eposta else False
                if eposta and not is_email_valid: st.warning("⚠️ Geçerli bir e-posta giriniz!")
            with c2: 
                soyad = st.text_input("Soyadınız")
                tel_in = st.text_input("Telefon Numaranız (05xx...)")
                is_tel_valid = bool(re.match(r'^(0?)[5][0-9]{9}$', tel_in)) if tel_in else False
                if tel_in and not is_tel_valid: st.warning("⚠️ Geçerli bir telefon giriniz!")
            
            sec_mud = st.selectbox("İlgili Müdürlük", tum_birimler)
            detay = st.text_area("Talep Detayı")
            if st.button("Talebi Kaydet"):
                if ad and soyad and is_email_valid and is_tel_valid:
                    sid = str(datetime.now().timestamp()).replace(".","")[-6:]
                    yeni = {"ID": sid, "Sıra_No": 1, "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": tel_temizle(tel_in), "Müdürlük": sec_mud, "Detay": detay.replace(","," "), "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"}
                    pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                    st.success(f"✅ Talebiniz alındı! ID: {sid}"); st.balloons()
                else: st.error("Lütfen formu doğru formatta doldurunuz.")

    # --- HIZLI İŞLEM: TALEP SORGULA ---
    elif st.session_state.sayfa == "talep_sorgu":
        st.markdown("### 🔍 Taleplerimi Görüntüle")
        if st.button("⬅️ Asistan Ana Menü"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        arama = st.text_input("E-posta veya Telefon numaranızı giriniz")
        if arama:
            temiz_arama = tel_temizle(arama)
            df = veri_yukle()
            if not df.empty:
                df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
                sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == temiz_arama)]
                if not sonuclar.empty:
                    st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
                else: st.warning("⚠️ Kayıt bulunamadı.")

    # --- HIZLI İŞLEM: SOHBET ---
    elif st.session_state.sayfa == "mudurluk_sohbet":
        st.markdown("### 💬 Müdürlükle Karşılıklı Sohbet")
        if st.button("⬅️ Asistan Ana Menü"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        m_sorgu = st.text_input("E-posta/Tel giriniz:")
        m_sifre = st.text_input("Sohbet Şifreniz:", type="password")
        if m_sorgu and m_sifre:
            df_m = mesaj_yukle()
            k_msg = df_m[((df_m["Gonderen"] == m_sorgu) | (df_m["Telefon"].apply(tel_temizle) == tel_temizle(m_sorgu))) & (df_m["Sifre"].astype(str) == str(m_sifre))]
            if not k_msg.empty:
                b_sec = st.radio("Birim Seç:", k_msg["Mudurluk"].unique(), horizontal=True)
                current = k_msg[k_msg["Mudurluk"] == b_sec]
                for _, r in current.iterrows():
                    with st.chat_message("user"): st.write(r['Mesaj'])
                    if r['Cevap'] != "Bekleniyor":
                        with st.chat_message("assistant"): st.write(r['Cevap'])
                with st.expander("Yanıt Yaz"):
                    with st.form("user_rep"):
                        msg = st.text_area("Mesaj:"); f = st.file_uploader("Belge:")
                        if st.form_submit_button("Gönder"):
                            pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": current.iloc[0]["Gonderen"], "Telefon": current.iloc[0]["Telefon"], "Sifre": m_sifre, "Mudurluk": b_sec, "Mesaj": msg, "Dosya_Adi": "Yok", "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                            st.rerun()
            else:
                st.info("💡 Henüz bir sohbetiniz yok. Yeni bir mesaj gönderin:")
                with st.form("new_chat"):
                    c_mud = st.selectbox("Birim", tum_birimler); c_mail = st.text_input("E-posta"); c_tel = st.text_input("Tel"); c_pass = st.text_input("Şifre Belirle"); c_txt = st.text_area("Mesaj")
                    if st.form_submit_button("Sohbeti Başlat"):
                        pd.DataFrame([{"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": c_mail, "Telefon": tel_temizle(c_tel), "Sifre": c_pass, "Mudurluk": c_mud, "Mesaj": c_txt, "Dosya_Adi": "Yok", "Cevap": "Bekleniyor", "Mudurluk_Dosya": "Yok"}]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                        st.success("Başlatıldı!"); st.rerun()

    # --- HIZLI İŞLEM: EVRAK REHBERİ ---
    elif st.session_state.sayfa == "evrak_rehberi":
        st.markdown("### 📄 Gerekli Evraklar")
        if st.button("⬅️ Asistan Ana Menü"): st.session_state.sayfa = "asistan_ana"; st.rerun()
        m_sec = st.selectbox("Müdürlük Seçin", tum_birimler)
        st.info(f"💡 {m_sec} için genel işlemler ve belgeler listeleniyor...")

# --- 🏢 3. EKRAN: MÜDÜRLÜK PORTALI ---
elif st.session_state.portal_modu == "mudurluk":
    if st.sidebar.button("🏠 Ana Ekrana Dön"): st.session_state.portal_modu = "karşılama"; st.rerun()
    st.markdown("### 🏢 Müdürlük Yönetim Paneli")
    c_a, c_b = st.columns(2)
    adm_b = c_a.selectbox("Biriminiz:", tum_birimler)
    adm_s = c_b.text_input("Yetkili Şifresi:", type="password")
    
    if adm_s == "1234":
        t1, t2 = st.tabs(["📋 Talepler", "💬 Sohbetler"])
        with t1:
            df_t = veri_yukle()
            if not df_t.empty:
                filt = df_t[df_t["Müdürlük"] == adm_b]
                if not filt.empty:
                    st.dataframe(filt, use_container_width=True)
                    sid = st.selectbox("ID Seç:", filt["ID"].tolist())
                    with st.container(border=True):
                        c1, c2 = st.columns(2)
                        yd = c1.selectbox("Durum:", ["İnceleniyor", "Tamamlandı", "Reddedildi", "Sevk Edildi"])
                        ys = c2.selectbox("Sevk:", tum_birimler, index=tum_birimler.index(adm_b))
                        ans = st.text_area("Yazılı Yanıt:")
                        if st.button("Güncelle ve Yanıtla"):
                            idx = df_t[df_t["ID"] == sid].index
                            df_t.at[idx[0], "Durum"] = yd if ys == adm_b else "Sevk Edildi"
                            df_t.at[idx[0], "Müdürlük"] = ys
                            df_t.at[idx[0], "Belediye_Cevabi"] = ans
                            df_t.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                            st.success("Güncellendi!"); st.rerun()
        with t2:
            df_m = mesaj_yukle()
            bm = df_m[df_m["Mudurluk"] == adm_b]
            ara = st.text_input("Vatandaş Ara (E-posta/Tel):")
            vl = [v for v in bm["Gonderen"].unique() if ara.lower() in str(v).lower()]
            if vl:
                vs = st.selectbox("Seç:", vl); vg = bm[bm["Gonderen"] == vs]
                for _, r in vg.iterrows():
                    st.info(f"👤 {r['Mesaj']}")
                    if r['Cevap'] != "Bekleniyor": st.success(f"🏛️ {r['Cevap']}")
                with st.form("adm_rep"):
                    a = st.text_area("Cevap:"); f = st.file_uploader("Belge Gönder")
                    if st.form_submit_button("Yanıtı Gönder"):
                        df_m.at[vg.index[-1], "Cevap"] = a; df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                        st.success("İletildi!"); st.rerun()
