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

# --- 📚 TÜM MÜDÜRLÜKLERİ KAPSAYAN EVRAK REHBERİ ---
EVRAK_REHBERI = {
    "İmar ve Şehircilik Müdürlüğü": {
        "İnşaat Ruhsatı": ["Tapu Kaydı", "Mimari Proje", "İmar Durum Belgesi", "Aplikasyon Krokisi"],
        "Yapı Kullanma İzin Belgesi (İskan)": ["Enerji Kimlik Belgesi", "Sığınak Raporu", "SGK İlişiksiz Belgesi"],
        "Numarataj İşlemleri": ["Tapu Fotokopisi", "Yapı Ruhsatı", "Kimlik Fotokopisi"]
    },
    "Yazı İşleri Müdürlüğü": {
        "Nikah Başvurusu": ["Sağlık Raporu", "4 Adet Fotoğraf", "Nüfus Kayıt Örneği", "Kimlik Aslı"],
        "Encümen Kararı Örneği": ["Dilekçe", "İlgili Kararın Tarih ve Sayısı"]
    },
    "Mali Hizmetler Müdürlüğü": {
        "Emlak Vergisi Bildirimi": ["Tapu Fotokopisi", "Kimlik Fotokopisi", "Kısıtlılık Belgesi (Varsa)"],
        "Rayiç Bedel Belgesi": ["Tapu Fotokopisi", "Borçsuzluk Yazısı", "İlgili Kişinin Kimliği"]
    },
    "Zabıta Müdürlüğü": {
        "İşyeri Açma ve Çalışma Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "İtfaiye Uygunluk Raporu", "Oda Kayıt Belgesi"],
        "Pazar Yeri Tahsisi": ["Oda Kayıt Belgesi", "İkametgah", "Sabıka Kaydı"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol ve Kaldırım Onarım Talebi": ["Konum Bilgisi", "Dilekçe veya Fotoğraflı Kanıt"],
        "Alt Yapı Kazı İzni": ["Proje Onayı", "AYKOME İzin Belgesi", "Teminat Dekontu"]
    }
}

BELEDİYE_İLETİŞİM = {
    "konum": "Pazar Mah. Atatürk Bulvarı No:165, Ondokuzmayıs/SAMSUN",
    "telefon": "0 (362) 511 44 88",
    "saat": "Hafta içi 08:30 - 17:30"
}

# --- SESSION STATE ---
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

sikayet_turleri_dict = {
    "Yazı İşleri Müdürlüğü": ["Evrak işlemleri", "Bilgi eksikliği", "Diğer"],
    "Veteriner İşleri Müdürlüğü": ["Sokak hayvanları", "Yaralı hayvan", "Diğer"],
    "Fen İşleri Müdürlüğü": ["Yol bozukluğu", "Kaldırım hasarı", "Diğer"],
    "Zabıta Müdürlüğü": ["Gürültü", "Kaldırım işgali", "Diğer"],
    "İmar ve Şehircilik Müdürlüğü": ["Ruhsat işlemleri", "Kaçak yapı", "Diğer"],
    "Mali Hizmetler Müdürlüğü": ["Vergi borcu", "Ödeme problemleri", "Diğer"]
}
tum_birimler = sorted(list(set(list(sikayet_turleri_dict.keys()) + list(EVRAK_REHBERI.keys()))))

# --- ÜST BAŞLIK VE LOGO ---
c1, c2 = st.columns([1, 6]) 
with c1:
    if os.path.exists("logo.jfif"): st.image("logo.jfif", width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Akıllı Vatandaş ve Yönetim Portalı")

st.divider()

# --- 🤖 BÖLÜM 1: AI ASİSTAN ---
if st.session_state.sayfa == "asistan":
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Size bugün nasıl yardımcı olabilirim?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("### Hızlı İşlemler")
    r1c1, r1c2, r1c3 = st.columns(3)
    if r1c1.button("📝 Şikayet Oluştur"): st.session_state.sayfa = "portal"; st.rerun()
    if r1c2.button("🔍 Şikayet Sorgulama"): st.session_state.sayfa = "portal"; st.rerun()
    if r1c3.button("📄 Evrak Rehberi"): st.session_state.evrak_aktif = True
    
    if st.button("🏢 Müdürlüğe Belge/Mesaj Gönder"): st.session_state.sayfa = "iletisim_kanali"; st.rerun()

    if "evrak_aktif" in st.session_state and st.session_state.evrak_aktif:
        m = st.selectbox("Müdürlük:", ["Seçiniz..."] + tum_birimler)
        if m in EVRAK_REHBERI:
            i = st.selectbox("İşlem:", list(EVRAK_REHBERI[m].keys()))
            for b in EVRAK_REHBERI[m][i]: st.write(f"✅ {b}")
        if st.button("Kapat"): del st.session_state.evrak_aktif; st.rerun()

# --- 🏢 BÖLÜM: İLETİŞİM KANALI ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlük İletişim Sistemi")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.form("direkt_iletisim", clear_on_submit=True):
        k_mud = st.selectbox("Birim:", tum_birimler)
        k_mail = st.text_input("E-posta:")
        k_sifre = st.text_input("Sorgulama Şifresi Belirleyin:", type="password")
        k_mesaj = st.text_area("Mesajınız:")
        k_dosya = st.file_uploader("Belge Seçin:")
        
        if st.form_submit_button("Gönder"):
            if k_mail and k_sifre and k_mesaj:
                dosya_adi = "Yok"
                if k_dosya:
                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                    dosya_adi = f"{datetime.now().strftime('%H%M%S')}_{k_dosya.name}"
                    with open(os.path.join("yuklenen_belgeler", dosya_adi), "wb") as f:
                        f.write(k_dosya.getbuffer())
                
                yeni = {"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Gonderen": k_mail, "Sifre": str(k_sifre), "Mudurluk": k_mud, "Mesaj": k_mesaj.replace(",","."), "Dosya_Adi": dosya_adi, "Cevap": "Bekleniyor"}
                pd.DataFrame([yeni]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                st.success("İletildi!")
            else: st.error("Eksik alan var.")

# --- 📝 BÖLÜM 2: PORTAL ---
elif st.session_state.sayfa == "portal":
    if st.button("⬅️ Geri"): st.session_state.sayfa = "asistan"; st.rerun()
    t1, t2 = st.tabs(["📝 Oluştur", "🔍 Sorgula"])
    
    with t1:
        st.write("Şikayet formunu doldurun...")
        # (Şikayet oluşturma kodun buraya gelecek - mevcut kodunla aynı)
        ad = st.text_input("Ad")
        soyad = st.text_input("Soyad")
        mail = st.text_input("E-posta")
        tel = st.text_input("Tel")
        mud = st.selectbox("Müdürlük", tum_birimler)
        detay = st.text_area("Detay")
        if st.button("Kaydet"):
            sid = str(datetime.now().timestamp()).replace(".","")[-6:]
            kayit = {"ID": sid, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Ad": ad, "Soyad": soyad, "E-posta": mail, "Telefon": tel, "Müdürlük": mud, "Detay": detay.replace(","," "), "Durum": "İnceleniyor", "Belediye_Cevabi": "Bekleniyor"}
            pd.DataFrame([kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
            st.success(f"ID: {sid}")

    with t2:
        arama = st.text_input("E-posta veya Tel Giriniz:")
        sorgu_sifre = st.text_input("Mesaj Şifreniz:", type="password")
        if arama:
            df_s = veri_yukle()
            if not df_s.empty: st.write("Şikayetleriniz:"), st.dataframe(df_s[df_s["E-posta"]==arama])
            
            df_m = mesaj_yukle()
            if not df_m.empty:
                kendi = df_m[(df_m["Gonderen"] == arama) & (df_m["Sifre"].astype(str) == str(sorgu_sifre))]
                if not kendi.empty: st.write("Mesaj Yanıtlarınız:"), st.dataframe(kendi[["Tarih", "Mudurluk", "Mesaj", "Cevap"]])

# --- 🏢 MÜDÜRLÜK YÖNETİM ---
st.divider()
with st.expander("🏢 Yetkili Girişi"):
    adm_b = st.selectbox("Birim:", tum_birimler)
    adm_s = st.text_input("Şifre:", type="password")
    
    if adm_s == "1234":
        at1, at2 = st.tabs(["📋 Şikayetler", "💬 Gelen Mesajlar & Belgeler"])
        
        with at1:
            df_a = veri_yukle()
            if not df_a.empty:
                filtre = df_a[df_a["Müdürlük"] == adm_b]
                st.dataframe(filtre)

        with at2:
            st.markdown(f"#### {adm_b} - Gelen Talepler")
            df_m = mesaj_yukle()
            if not df_m.empty:
                birim_msj = df_m[df_m["Mudurluk"] == adm_b]
                if not birim_msj.empty:
                    for idx, row in birim_msj.iterrows():
                        with st.container(border=True):
                            st.markdown(f"📧 **Gönderen:** `{row['Gonderen']}`")
                            st.write(f"📅 **Tarih:** {row['Tarih']}")
                            st.info(f"💬 **Mesaj:** {row['Mesaj']}")
                            
                            if 'Dosya_Adi' in row and str(row['Dosya_Adi']) != "Yok":
                                yol = os.path.join("yuklenen_belgeler", str(row['Dosya_Adi']))
                                if os.path.exists(yol):
                                    with open(yol, "rb") as f:
                                        st.markdown(dosya_indirme_linki(f.read(), str(row['Dosya_Adi'])), unsafe_allow_html=True)
                                else: st.warning("Dosya bulunamadı.")
                            
                            yanit_alanı = st.text_area("Yanıtınız:", value=row['Cevap'] if row['Cevap'] != "Bekleniyor" else "", key=f"y_{idx}")
                            if st.button("Yanıtı Gönder", key=f"b_{idx}"):
                                df_m.at[idx, "Cevap"] = yanit_alanı
                                df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                                st.success("Gönderildi!"); st.rerun()
                else: st.info("Mesaj yok.")
