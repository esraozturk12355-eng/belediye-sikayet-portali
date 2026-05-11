import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime, timedelta

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Ondokuzmayıs Belediyesi Portal", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏛️"
)

# --- DOSYA İNDİRME VE GÖRÜNTÜLEME FONKSİYONU ---
def dosya_indirme_linki(dosya_yolu, dosya_adi, etiket="İndir"):
    if os.path.exists(dosya_yolu):
        with open(dosya_yolu, "rb") as f:
            dosya_verisi = f.read()
        b64 = base64.b64encode(dosya_verisi).decode()
        # İndirme butonu stilinde HTML linki
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}" style="text-decoration:none; background-color:#007BFF; color:white; padding:5px 10px; border-radius:5px; font-size:13px;">📩 {etiket}: {dosya_adi}</a>'
    return "⚠️ Dosya bulunamadı."

# --- SESSION STATE ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str}, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    cols = ["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Kimden"]
    if os.path.exists("mesajlar.csv"):
        try: 
            df = pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
            for col in cols:
                if col not in df.columns: df[col] = "Yok"
            return df
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

tum_birimler = ["Destek Hizmetleri", "Emlak ve İstimlak", "Fen İşleri", "Mali Hizmetler", "Veteriner İşleri", "Yapı Kontrol", "Yazı İşleri", "Zabıta", "İklim Değişikliği ve Sıfır Atık", "İmar ve Şehircilik"]

# --- ÜST BAŞLIK ---
c1, c2 = st.columns([1, 6]) 
if os.path.exists("logo.jfif"): c1.image("logo.jfif", width=120)
c2.title("Ondokuzmayıs Belediyesi")
c2.subheader("Vatandaş İletişim & Dosya Paylaşım Portalı")
st.divider()

# --- 🤖 1. SAYFA: ASİSTAN ---
if st.session_state.sayfa == "asistan":
    st.markdown("### 🤖 Akıllı Asistan")
    col1, col2, col3 = st.columns(3)
    if col1.button("📝 Talep ve Öneri Bildir", use_container_width=True): st.session_state.sayfa = "talep_ekrani"; st.rerun()
    if col2.button("🔍 Talep Sorgulama", use_container_width=True): st.session_state.sayfa = "sorgu_ekrani"; st.rerun()
    if col3.button("💬 Müdürlük Sohbet & Belge Gönder", use_container_width=True): st.session_state.sayfa = "sohbet_ekrani"; st.rerun()

# --- 📝 2. SAYFA: TALEP ---
elif st.session_state.sayfa == "talep_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    with st.form("talep_form"):
        v_ad = st.text_input("Ad Soyad")
        v_mail = st.text_input("E-posta")
        v_mud = st.selectbox("Müdürlük", tum_birimler)
        v_detay = st.text_area("Mesajınız")
        if st.form_submit_button("Talebi İlet"):
            sid = str(datetime.now().timestamp()).replace(".","")[-6:]
            yeni = {"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": v_ad, "E-posta": v_mail, "Müdürlük": v_mud, "Detay": v_detay, "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"}
            pd.DataFrame([yeni]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            st.success(f"Başvurunuz alındı. Takip ID: {sid}")

# --- 🔍 3. SAYFA: SORGULAMA ---
elif st.session_state.sayfa == "sorgu_ekrani":
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    s_mail = st.text_input("Sorgulama için E-posta giriniz:")
    if s_mail:
        df_s = veri_yukle()
        if not df_s.empty:
            res = df_s[df_s["E-posta"] == s_mail]
            if not res.empty: st.dataframe(res[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
            else: st.warning("Bu e-posta ile kayıt bulunamadı.")

# --- 💬 4. SAYFA: KARŞILIKLI SOHBET VE BELGE PAYLAŞIMI ---
elif st.session_state.sayfa == "sohbet_ekrani":
    st.markdown("### 💬 Müdürlük Sohbet & Belge Havuzu")
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    cl, cr = st.columns([1, 2])
    with cl:
        u_mail = st.text_input("E-posta Adresiniz:")
        u_sifre = st.text_input("Sohbet Şifreniz:", type="password")
        u_mud = st.selectbox("Birim Seçiniz:", tum_birimler)
    
    if u_mail and u_sifre:
        df_m = mesaj_yukle()
        sohbet_gecmisi = df_m[(df_m["Gonderen"] == u_mail) & (df_m["Sifre"].astype(str) == str(u_sifre))]
        
        with cr:
            st.markdown(f"**Sohbet: {u_mail}**")
            chat_box = st.container(height=450, border=True)
            with chat_box:
                if sohbet_gecmisi.empty:
                    st.info("Sohbeti başlatmak için aşağıdan mesaj yazın.")
                else:
                    for _, row in sohbet_gecmisi.iterrows():
                        is_user = row["Kimden"] == "Vatandaş"
                        with st.chat_message("user" if is_user else "assistant"):
                            st.write(f"**{row['Kimden']}** ({row['Tarih']})")
                            st.write(row['Mesaj'])
                            # Belge Paylaşımı Kontrolü
                            if row['Dosya_Adi'] != "Yok":
                                klasor = "yuklenen_belgeler" if is_user else "belediye_belgeleri"
                                dosya_yolu = os.path.join(klasor, str(row['Dosya_Adi']))
                                st.markdown(dosya_indirme_linki(dosya_yolu, str(row['Dosya_Adi']), "Ekli Dosya"), unsafe_allow_html=True)

            # Vatandaş Mesaj Yazma Alanı
            with st.form("vatandas_form", clear_on_submit=True):
                v_msg = st.text_area("Cevabınız / Sorunuz:")
                v_file = st.file_uploader("Belge/Görsel Ekle:")
                if st.form_submit_button("Gönder"):
                    if v_msg or v_file:
                        fn = "Yok"
                        if v_file:
                            if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                            fn = f"vatandas_{datetime.now().strftime('%H%M%S')}_{v_file.name}"
                            with open(os.path.join("yuklenen_belgeler", fn), "wb") as f: f.write(v_file.getbuffer())
                        
                        yeni_satir = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": u_mail, "Sifre": str(u_sifre), "Mudurluk": u_mud, "Mesaj": v_msg, "Dosya_Adi": fn, "Kimden": "Vatandaş"}
                        pd.DataFrame([yeni_satir]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                        st.rerun()

# --- 🏢 MÜDÜRLÜK YÖNETİM PANELİ (ADMIN) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli (Yetkili)"):
    adm_b = st.selectbox("Müdürlüğünüz:", tum_birimler, key="ab")
    adm_s = st.text_input("Panel Şifresi:", type="password", key="as")
    
    if adm_s == "1234":
        df_all = mesaj_yukle()
        b_mesajlari = df_all[df_all["Mudurluk"] == adm_b]
        v_listesi = b_mesajlari["Gonderen"].unique()
        
        if len(v_listesi) > 0:
            v_sec = st.selectbox("Sohbet Seçiniz:", v_listesi)
            v_detay = b_mesajlari[b_mesajlari["Gonderen"] == v_sec]
            
            # Sohbet Akışı
            for _, sm in v_detay.iterrows():
                with st.chat_message("user" if sm["Kimden"] == "Vatandaş" else "assistant"):
                    st.write(f"**{sm['Kimden']}** ({sm['Tarih']})")
                    st.write(sm['Mesaj'])
                    if sm['Dosya_Adi'] != "Yok":
                        yol = "yuklenen_belgeler" if sm["Kimden"] == "Vatandaş" else "belediye_belgeleri"
                        st.markdown(dosya_indirme_linki(os.path.join(yol, str(sm['Dosya_Adi'])), str(sm['Dosya_Adi']), "Dosyayı İndir"), unsafe_allow_html=True)
            
            # Müdürlük Cevap Formu
            with st.form("adm_reply_form"):
                a_msg = st.text_area("Vatandaşa Yanıtınız:")
                a_file = st.file_uploader("Belge/Görsel Gönder:")
                if st.form_submit_button("Yanıtı ve Dosyayı Gönder"):
                    afn = "Yok"
                    if a_file:
                        if not os.path.exists("belediye_belgeleri"): os.makedirs("belediye_belgeleri")
                        afn = f"belediye_{datetime.now().strftime('%H%M')}_{a_file.name}"
                        with open(os.path.join("belediye_belgeleri", afn), "wb") as f: f.write(a_file.getbuffer())
                    
                    yeni_yanit = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": v_sec, "Sifre": v_detay.iloc[0]["Sifre"], "Mudurluk": adm_b, "Mesaj": a_msg, "Dosya_Adi": afn, "Kimden": "Müdürlük"}
                    pd.DataFrame([yeni_yanit]).to_csv("mesajlar.csv", mode='a', header=False, index=False, encoding="utf-8-sig")
                    st.success("Mesaj iletildi."); st.rerun()
        else:
            st.info("Bu müdürlüğe ait henüz bir sohbet kaydı bulunmamaktadır.")
