# --- 🔍 4. SAYFA: SORGULAMA VE SOHBET ---
elif st.session_state.sayfa == "sorgu_ekrani":
    # ... (üst kısımlar aynı)
    if arama:
        temiz_arama = tel_temizle(arama) # Girişi temizle
        
        # 1. Şikayet Kayıtlarını Göster
        df_s = veri_yukle()
        if not df_s.empty:
            # Hem e-posta hem de temizlenmiş telefon üzerinden karşılaştırma yap
            res = df_s[(df_s["E-posta"] == arama) | (df_s["Telefon"].apply(tel_temizle) == temiz_arama)]
            if not res.empty:
                st.table(res[["Tarih", "Müdürlük", "Durum", "Belediye_Cevabi"]])
        
        # 2. Mesajlaşma Geçmişini Göster
        df_m = mesaj_yukle()
        if not df_m.empty:
            # Mesajlar tablosunda da hem e-posta hem temizlenmiş telefon kontrolü
            kendi_msgs = df_m[((df_m["Gonderen"] == arama) | (df_m["Telefon"].apply(tel_temizle) == temiz_arama)) & (df_m["Sifre"].astype(str) == str(sifre_chat))]
            # ... (devamı aynı)
