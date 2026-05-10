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
    },
    "Veteriner İşleri Müdürlüğü": {
        "Sahipli Hayvan Kayıt": ["Hayvan Pasaportu", "Kuduz Aşısı Karnesi", "Çip Numarası"],
        "Sokak Hayvanı Tedavi Talebi": ["İhbar Dilekçesi", "Konum Bilgisi"]
    },
    "Emlak ve İstimlak Müdürlüğü": {
        "Taşınmaz Kiralama": ["İhale Şartnamesi", "Geçici Teminat Makbuzu", "İkametgah"],
        "Yer Tahsis Talebi": ["Kurumsal Yazı veya Şahsi Dilekçe", "Kullanım Amacı Belgesi"]
    },
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü": {
        "Atık Pil/Yağ Toplama Talebi": ["Adres Bilgisi", "İletişim Numarası"],
        "Geri Dönüşüm Konteynırı": ["Dilekçe", "Bina Sakinleri İmzası (Gerekirse)"]
    },
    "Yapı Kontrol Müdürlüğü": {
        "Yapı Denetim Onayı": ["Hakediş Raporu", "Laboratuvar Sonuçları"],
        "Kaçak Yapı İhbar": ["Ada/Parsel Bilgisi", "Olay Yeri Fotoğrafı"]
    },
    "Destek Hizmetleri Müdürlüğü": {
        "İhale Dosya Alımı": ["Firma İmza Sirküleri", "Vezne Makbuzu"],
        "Tedarikçi Kaydı": ["Vergi Levhası", "Ticaret Sicil Gazetesi"]
    }
}

BELEDİYE_İLETİŞİM = {
    "konum": "Pazar Mah. Atatürk Bulvarı No:165, Ondokuzmayıs/SAMSUN",
    "telefon": "0 (362) 511 44 88",
    "saat": "Hafta içi 08:00 - 17:00"
}

# --- SESSION STATE ---
if "sayfa" not in st.session_state: st.session_state.sayfa = "asistan"
if "messages" not in st.session_state: st.session_state.messages = []

# --- ÜST BAŞLIK VE LOGO ALANI ---
c1, c2 = st.columns([1, 6]) 
with c1:
    logo_dosyasi = "logo.jfif"
    if os.path.exists(logo_dosyasi): st.image(logo_dosyasi, width=120)
    else: st.write("# 🏛️") 
with c2:
    st.title("Ondokuzmayıs Belediyesi")
    st.subheader("Şikayet Yönetim Portalı")

# --- FONKSİYONLAR ---
def veri_yukle():
    if os.path.exists("sikayetler.csv"):
        try: return pd.read_csv("sikayetler.csv", dtype={'ID': str, 'Telefon': str}, on_bad_lines='skip', index_col=False, encoding="utf-8-sig")
        except: return pd.DataFrame()
    return pd.DataFrame()

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

# --- 🤖 BÖLÜM 1: AI ASİSTAN VE EVRAK REHBERİ ---
if st.session_state.sayfa == "asistan":
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Merhaba! Ondokuzmayıs Belediyesi Akıllı Asistanına hoş geldiniz. 😊 Size bugün nasıl yardımcı olabilirim?"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.write("### Hızlı İşlemler")
    r1c1, r1c2, r1c3 = st.columns(3)
    
    if r1c1.button("📝 Şikayet Oluştur"):
        st.session_state.messages.append({"role": "assistant", "content": "Anlaşıldı, sizi hemen şikayet formuna yönlendiriyorum..."})
        st.session_state.sayfa = "portal"; st.rerun()

    if r1c2.button("🔍 Şikayet Sorgulama"):
        st.session_state.messages.append({"role": "assistant", "content": "Sorgulama ekranına yönlendiriliyorsunuz..."})
        st.session_state.sayfa = "portal"; st.rerun()

    if r1c3.button("📄 Evrak & Bilgi Rehberi"):
        st.session_state.evrak_aktif = True

    if st.button("📞 Belediye İletişim Bilgileri"):
        ans = f"📞 **Tel:** {BELEDİYE_İLETİŞİM['telefon']} \n📍 **Adres:** {BELEDİYE_İLETİŞİM['konum']} \n⏰ **Mesai:** {BELEDİYE_İLETİŞİM['saat']}"
        st.session_state.messages.append({"role": "assistant", "content": ans}); st.rerun()

    if "evrak_aktif" in st.session_state and st.session_state.evrak_aktif:
        st.write("---")
        st.markdown("#### 📂 Müdürlük Evrak Listeleri")
        m = st.selectbox("Lütfen Müdürlük seçiniz:", ["Seçiniz..."] + sorted(list(EVRAK_REHBERI.keys())))
        if m != "Seçiniz...":
            i = st.selectbox("İşlem seçiniz:", ["Seçiniz..."] + list(EVRAK_REHBERI[m].keys()))
            if i != "Seçiniz...":
                st.info(f"**{i}** için gerekli belgeler:")
                for b in EVRAK_REHBERI[m][i]: st.write(f"✅ {b}")
        if st.button("Rehberi Kapat"): del st.session_state.evrak_aktif; st.rerun()

    if prompt := st.chat_input("Mesajınızı yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        p_low = prompt.lower()
        if any(x in p_low for x in ["şikayet", "sikayet", "oluştur"]):
            st.session_state.messages.append({"role": "assistant", "content": "Sizi yönlendiriyorum..."})
            st.session_state.sayfa = "portal"; st.rerun()
        else:
            st.session_state.messages.append({"role": "assistant", "content": "Size şikayet kaydı veya evraklar konusunda yardımcı olabilirim."})
            st.rerun()

# --- 📝 BÖLÜM 2: ANA PORTAL ---
elif st.session_state.sayfa == "portal":
    if st.button("⬅️ Asistana Geri Dön"):
        st.session_state.sayfa = "asistan"; st.rerun()

    tab1, tab2 = st.tabs(["📝 Yeni Şikayet Oluştur", "🔍 Şikayetlerimi Görüntüle"])

    with tab1:
        st.markdown("### 📝 Yeni Şikayet Formu")
        c1, c2 = st.columns(2)
        with c1:
            ad = st.text_input("Adınız", key="ad_yeni")
            eposta = st.text_input("E-posta Adresiniz", key="mail_yeni")
            email_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail|hotmail|outlook|icloud|yandex|yahoo|windowslive)\.(com|com\.tr|net)$'
            is_email_valid = False
            if eposta != "" and re.match(email_pattern, eposta, re.IGNORECASE):
                st.success("E-posta formatı geçerli. ✅"); is_email_valid = True
            elif eposta != "": st.warning("⚠️ Lütfen geçerli bir e-posta adresi giriniz!")

        with c2: 
            soyad = st.text_input("Soyadınız", key="soyad_yeni")
            telefon_input = st.text_input("Telefon Numaranız", key="tel_yeni")
        
        secilen_mudurluk = st.selectbox("İlgili Müdürlüğü Seçiniz", tum_birimler, key="mud_yeni")
        tur_listesi = sikayet_turleri_dict.get(secilen_mudurluk, ["Genel Şikayet", "Diğer"])
        sikayet_turu = st.selectbox("Şikayet Türü", tur_listesi, key="tur_yeni")
        detay = st.text_area("Şikayet Detayı", key="detay_yeni")
        
        if st.button("Şikayeti Kaydet"):
            if ad and soyad and eposta and is_email_valid and telefon_input:
                temiz_tel = tel_temizle(telefon_input)
                df_mevcut = veri_yukle()
                yeni_sira_no = 1
                if not df_mevcut.empty and "Müdürlük" in df_mevcut.columns and "Sıra_No" in df_mevcut.columns:
                    birim_kayitlari = df_mevcut[df_mevcut["Müdürlük"] == secilen_mudurluk]
                    if not birim_kayitlari.empty: yeni_sira_no = int(birim_kayitlari["Sıra_No"].max()) + 1
                
                sikayet_id = str(datetime.now().timestamp()).replace(".","")[-6:]
                yeni_kayit = {
                    "ID": sikayet_id, "Sıra_No": yeni_sira_no, "Tarih": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                    "Ad": ad, "Soyad": soyad, "E-posta": eposta, "Telefon": temiz_tel,
                    "Müdürlük": secilen_mudurluk, "Tür": sikayet_turu, "Detay": detay.replace(",", " "), 
                    "Durum": "İnceleniyor", "Belediye_Cevabi": "Henüz cevaplanmadı"
                }
                pd.DataFrame([yeni_kayit]).to_csv("sikayetler.csv", mode='a', header=not os.path.exists("sikayetler.csv"), index=False, encoding="utf-8-sig")
                st.success(f"✅ Şikayet Alındı. ID: {sikayet_id}"); st.balloons()
            else: st.error("Lütfen formu eksiksiz doldurunuz.")

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
                    st.table(sonuclar[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
                else: st.warning("Kayıt bulunamadı.")
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
        if not df_admin.empty:
            if "Müdürlük" in df_admin.columns:
                filtreli = df_admin[df_admin["Müdürlük"] == admin_birim].sort_values(by="Sıra_No")
                if not filtreli.empty:
                    st.dataframe(filtreli[["Sıra_No", "ID", "Tarih", "Ad", "Soyad", "Telefon", "Durum", "Detay", "Belediye_Cevabi"]])
                    st.write("---")
                    secilen_id = st.selectbox("İşlem Yapılacak ID Seçiniz:", filtreli["ID"].tolist(), key="islem_id")
                    
                    ci1, ci2 = st.columns(2)
                    with ci1:
                        yeni_durum = st.selectbox("Durum Güncelle:", ["İnceleniyor", "İşleme Alındı", "Tamamlandı", "Reddedildi"], key="durum_up")
                        yonlendir = st.selectbox("Başka Birime Yönlendir:", tum_birimler, index=tum_birimler.index(admin_birim), key="yonlendir_up")
                    with ci2:
                        cevap_notu = st.text_area("Cevap Notu:", key="cevap_up")
                    
                    if st.button("Değişiklikleri Onayla"):
                        idx = df_admin[df_admin["ID"] == secilen_id].index
                        if not idx.empty:
                            # Eğer müdürlük yönlendirmesi yapıldıysa yeni birimin en sonuna ekle
                            if df_admin.at[idx[0], "Müdürlük"] != yonlendir:
                                hedef = df_admin[df_admin["Müdürlük"] == yonlendir]
                                df_admin.at[idx[0], "Sıra_No"] = 1 if hedef.empty else hedef["Sıra_No"].max() + 1
                            
                            df_admin.at[idx[0], "Durum"] = yeni_durum
                            df_admin.at[idx[0], "Müdürlük"] = yonlendir
                            df_admin.at[idx[0], "Belediye_Cevabi"] = cevap_notu
                            df_admin.to_csv("sikayetler.csv", index=False, encoding="utf-8-sig")
                            
                            st.success("Kayıt başarıyla güncellendi!")
                            st.rerun()
                else:
                    st.info(f"{admin_birim} için henüz kayıtlı bir şikayet bulunmuyor.")

