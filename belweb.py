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
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{dosya_adi}">📩 {dosya_adi} İndir</a>'

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
        "İşyeri Açma ve Çalışma Ruhsatı": ["Kira Kontratı", "Vergi Levhası", "İtfaiye Uygunluk Raporu", "Oda Kayıt Belgesi"]
    },
    "Fen İşleri Müdürlüğü": {
        "Yol ve Kaldırım Onarım Talebi": ["Konum Bilgisi", "Dilekçe veya Fotoğraflı Kanıt"]
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kayıt": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi", "Çip Numarası"]
    },
    "Emlak ve İstimlak Müdürlüğü": {
        "Taşınmaz Kiralama": ["İhale Şartnamesi", "Geçici Teminat Makbuzu", "İkametgah"]
    },
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": {
        "Atık Pil/Yağ Toplama Talebi": ["Adres Bilgisi", "İletişim Numarası"]
    },
    "Yapı Kontrol Müdürlüğü": {
        "Yapı Denetim Onayı": ["Hakediş Raporu", "Laboratuvar Sonuçları"]
    },
    "Destek Hizmetleri Müdürlüğü": {
        "İhale Dosya Alımı": ["Firma İmza Sirküleri", "Vezne Makbuzu"]
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

# --- ÜST BAŞLIK VE LOGO ---
c1, c2 = st.columns([1, 6]) 
with c1:
    logo_dosyasi = "logo.jfif"
    if os.path.exists(logo_dosyasi): st.image(logo_dosyasi, width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Akıllı Vatandaş ve Yönetim Portalı")

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

def mesaj_yukle():
    if os.path.exists("mesajlar.csv"):
        return pd.read_csv("mesajlar.csv", encoding="utf-8-sig")
    return pd.DataFrame(columns=["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap"])

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

st.divider()

# --- 🤖 BÖLÜM 1: AI ASİSTAN ---
if st.session_state.sayfa == "asistan":
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Ben Akıllı Asistan. 😊 Size bugün nasıl yardımcı olabilirim?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("### Hızlı İşlemler")
    r1c1, r1c2, r1c3 = st.columns(3)
    r2c1, r2c2 = st.columns(2)
    
    if r1c1.button("📝 Şikayet Oluştur"):
        st.session_state.sayfa = "portal"; st.rerun()
    if r1c2.button("🔍 Şikayet Sorgulama"):
        st.session_state.sayfa = "portal"; st.rerun()
    if r1c3.button("📄 Evrak & Bilgi Rehberi"):
        st.session_state.evrak_aktif = True
    if r2c1.button("🏢 Müdürlük ile Doğrudan İletişim"):
        st.session_state.sayfa = "iletisim_kanali"; st.rerun()
    if r2c2.button("📞 İletişim Bilgileri"):
        ans = f"📞 **Tel:** {BELEDİYE_İLETİŞİM['telefon']} \n📍 **Adres:** {BELEDİYE_İLETİŞİM['konum']}"
        st.session_state.messages.append({"role": "assistant", "content": ans}); st.rerun()

    if "evrak_aktif" in st.session_state and st.session_state.evrak_aktif:
        st.write("---")
        m = st.selectbox("Müdürlük seçiniz:", ["Seçiniz..."] + sorted(list(EVRAK_REHBERI.keys())))
        if m != "Seçiniz...":
            i = st.selectbox("İşlem seçiniz:", ["Seçiniz..."] + list(EVRAK_REHBERI[m].keys()))
            if i != "Seçiniz...":
                st.info(f"**{i}** için gerekli belgeler:")
                for b in EVRAK_REHBERI[m][i]: st.write(f"✅ {b}")
        if st.button("Rehberi Kapat"): del st.session_state.evrak_aktif; st.rerun()

# --- 🏢 BÖLÜM: MÜDÜRLÜK İLETİŞİM KANALI ---
elif st.session_state.sayfa == "iletisim_kanali":
    st.markdown("### 🏢 Müdürlük İletişim ve Belge Gönderim Sistemi")
    if st.button("⬅️ Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    
    with st.form("direkt_iletisim", clear_on_submit=True):
        k_mud = st.selectbox("İletişime Geçilecek Müdürlük:", tum_birimler)
        k_mail = st.text_input("E-posta Adresiniz:")
        k_sifre_belirle = st.text_input("Bu işlem için bir şifre belirleyiniz:", type="password", help="Yanıtı kontrol ederken bu şifreyi kullanacaksınız.")
        k_mesaj = st.text_area("Mesajınız:")
        k_dosya = st.file_uploader("Belge Yükle (PDF, PNG, JPG):")
        submit_msg = st.form_submit_button("Mesajı ve Belgeyi Gönder")
        
        if submit_msg:
            if k_mail and k_sifre_belirle and k_mesaj:
                # Dosya Saklama (Klasör yoksa oluştur)
                dosya_adi = "Yok"
                if k_dosya:
                    if not os.path.exists("yuklenen_belgeler"): os.makedirs("yuklenen_belgeler")
                    dosya_adi = f"{datetime.now().strftime('%H%M%S')}_{k_dosya.name}"
                    with open(os.path.join("yuklenen_belgeler", dosya_adi), "wb") as f:
                        f.write(k_dosya.getbuffer())

                yeni_mesaj = {
                    "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Gonderen": k_mail, "Sifre": k_sifre_belirle, "Mudurluk": k_mud, 
                    "Mesaj": k_mesaj, "Dosya_Adi": dosya_adi, "Cevap": "Bekleniyor"
                }
                pd.DataFrame([yeni_mesaj]).to_csv("mesajlar.csv", mode='a', header=not os.path.exists("mesajlar.csv"), index=False, encoding="utf-8-sig")
                st.success("Talebiniz iletildi. Sorgulama ekranından şifrenizle takip edebilirsiniz.")
            else: st.error("Lütfen tüm alanları doldurunuz.")

# --- 📝 BÖLÜM 2: ANA PORTAL ---
elif st.session_state.sayfa == "portal":
    if st.button("⬅️ Asistana Geri Dön"): st.session_state.sayfa = "asistan"; st.rerun()
    t1, t2 = st.tabs(["📝 Yeni Şikayet", "🔍 Sorgulama"])

    with t1:
        # (Senin orijinal şikayet formu kodun buraya gelir - Değişmedi)
        st.markdown("### Şikayet Formu")
        # ... (Önceki şikayet formu akışı)

    with t2:
        st.markdown("### 🔍 Takip Paneli")
        arama = st.text_input("E-posta veya Telefon numaranız:")
        sorgu_sifre = st.text_input("İletişim Şifreniz (Eğer mesaj attıysanız):", type="password")
        
        if arama:
            df = veri_yukle()
            if not df.empty:
                df['Telefon_Temiz'] = df['Telefon'].apply(tel_temizle)
                sonuclar = df[(df["E-posta"] == arama) | (df["Telefon_Temiz"] == tel_temizle(arama))]
                if not sonuclar.empty: st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])

            # Mesaj Yanıtları (Kullanıcının kendi belirlediği şifre ile kontrol)
            df_m = mesaj_yukle()
            if not df_m.empty:
                kendi_msj = df_m[(df_m["Gonderen"] == arama) & (df_m["Sifre"].astype(str) == sorgu_sifre)]
                if not kendi_msj.empty:
                    st.write("---")
                    st.markdown("#### 💬 Mesajlarınıza Gelen Cevaplar")
                    st.dataframe(kendi_msj[["Tarih", "Mudurluk", "Mesaj", "Cevap"]])

# --- 🏢 BÖLÜM 3: MÜDÜRLÜK PANELİ (ADMIN) ---
st.divider()
with st.expander("🏢 Müdürlük Yönetim Paneli"):
    cp1, cp2 = st.columns(2)
    with cp1: admin_birim = st.selectbox("Birim Seçiniz:", tum_birimler, key="adm_birim")
    with cp2: sifre = st.text_input("Şifre:", type="password", key="adm_pass")
    
    if sifre == "1234":
        at1, at2 = st.tabs(["📋 Şikayetler", "💬 Vatandaşla İletişim & Belgeler"])
        
        with at1:
            df_a = veri_yukle()
            if not df_a.empty:
                filtre = df_a[df_a["Müdürlük"] == admin_birim]
                st.dataframe(filtre)

        with at2:
            st.markdown(f"#### {admin_birim} - Gelen Mesajlar")
            df_m = mesaj_yukle()
            if not df_m.empty:
                birim_msj = df_m[df_m["Mudurluk"] == admin_birim]
                if not birim_msj.empty:
                    for index, row in birim_msj.iterrows():
                        with st.container(border=True):
                            st.write(f"**Gönderen:** {row['Gonderen']} | **Tarih:** {row['Tarih']}")
                            st.write(f"**Mesaj:** {row['Mesaj']}")
                            
                            # --- BELGE GÖRÜNTÜLEME VE İNDİRME ---
                            if row['Dosya_Adi'] != "Yok":
                                yol = os.path.join("yuklenen_belgeler", row['Dosya_Adi'])
                                if os.path.exists(yol):
                                    with open(yol, "rb") as f:
                                        st.markdown(dosya_indirme_linki(f.read(), row['Dosya_Adi']), unsafe_allow_html=True)
                            
                            adm_yanit = st.text_area("Yanıtınız:", key=f"yanit_{index}")
                            if st.button("Yanıtı Gönder", key=f"btn_{index}"):
                                df_m.at[index, "Cevap"] = adm_yanit
                                df_m.to_csv("mesajlar.csv", index=False, encoding="utf-8-sig")
                                st.success("Yanıt iletildi!"); st.rerun()
                else: st.info("Gelen mesaj yok.")
