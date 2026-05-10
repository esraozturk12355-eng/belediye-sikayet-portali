# --- MESAJ YÜKLEME FONKSİYONU (GÜNCELLENDİ) ---
def mesaj_yukle():
    if os.path.exists("mesajlar.csv"):
        try:
            # on_bad_lines='skip' sayesinde hatalı satırlar uygulamayı çökertmez
            return pd.read_csv("mesajlar.csv", on_bad_lines='skip', encoding="utf-8-sig")
        except:
            return pd.DataFrame(columns=["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap"])
    return pd.DataFrame(columns=["Tarih", "Gonderen", "Sifre", "Mudurluk", "Mesaj", "Dosya_Adi", "Cevap"])

# --- KAYIT KISMINDAKİ KÜÇÜK DÜZELTME ---
# (iletisim_kanali bölümünde yeni_mesaj oluşturulan yer)
# Mesajın içindeki virgülleri noktaya çeviriyoruz ki CSV yapısı bozulmasın
temiz_mesaj = k_mesaj.replace(",", ".") 

yeni_mesaj = {
    "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "Gonderen": k_mail, 
    "Sifre": str(k_sifre_belirle), # Şifreyi string olarak saklamak daha güvenlidir
    "Mudurluk": k_mud, 
    "Mesaj": temiz_mesaj, # Virgüllerden temizlenmiş mesaj
    "Dosya_Adi": dosya_adi, 
    "Cevap": "Bekleniyor"
}
