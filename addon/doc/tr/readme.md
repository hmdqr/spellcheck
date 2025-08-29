# Yazım Denetimi

- Yazarlar: Fawaz Abdulrahman <fawaz.ar94@gmail.com> ve  
- Musharraf Omer <ibnomer2011@hotmail.com>  
- Sürüm: 1.5
- Sürümler: https://github.com/hmdqr/spellcheck/releases  

Not (resmî olmayan çatallanma/bakım): Bu depo, eklentiyi modern NVDA’da çalıştırmak amacıyla hmdqr tarafından bakımı yapılan resmî olmayan bir fork’tur. Resmî depo: https://github.com/blindpandas/spellcheck. hmdqr tarafından özgün kod yazımı yoktur; yalnızca uyumluluk, paketleme ve belgeler GitHub Copilot yardımıyla güncellendi.

## Hakkında:  

Eklentinin amacı metindeki yazım hatalarını hızlı bir şekilde bulup düzeltebilmemize imkan sağlamaktır.  
Ayrıca, Sözlükte bulunmayan kelimeleri ekleyebileceğiniz kişisel bir kelime listesi de oluşturabilirsiniz.  

## Kullanım:  

- Denetlemek istediğiniz metnin tümünü CTRL+A ile seçmeli veya dilediğiniz bir kısmını diğer seçme yöntemleri ile seçmelisiniz.  
- Eklenti arayüzünü çağırmak için NVDA+Alt+S tuşlarına basın.  
- Yazım denetimi varsayılan yazma dilinize göre yapılacaktır.  
- Alternatif olarak, NVDA+ALT+SHIFT+L tuşlarına basarak açılacak listeden dilediğiniz dili seçebilirsiniz.  
- hata yoksa yazım hatası olmadığını belirten bir mesaj duyurusu yapılır.  
- hata olması durumunda, yanlış yazılan kelimeler arasında gezinmek için sağ ve sol yön tuşlarını, Öneri listesini açmak için Enter veya aşağı yön tuşunu kullanın.  
- Öneri listesinde Aşağı ve yukarı yön tuşları ile gezebilir, dilediğiniz öneriyi seçtikten sonra Enter tuşu ile ilgili öneriyi uygulayabilirsiniz. Sağ ve Sol yön tuşları ile hatalı kelimeler arasında gezinirken, NVDA öneri listesinden seçtiğiniz kelimeyi de seslendirecektir.  
 - İpucu: Odaktaki yanlış yazım/öneriyi harf harf okumak için Control+Shift+P tuşlarına basın.
- Sağ ve sol yön tuşları ile hatalar arasında gezinirken, seçilen bir öneriyi kaldırmak için Geri Silme(Back Space) tuşuna basabilirsiniz.  
- Bittiğinde, vurgulanan metinde seçilen önerileri değiştirmek için Control+R tuşlarına basın.  
- Control+r, sözcükleri değiştirmeye ek olarak, bu seçeneği işaretlediyseniz sözcüğü kişisel sözlüğe de ekler.  

### kişisel sözlük:

öneriler menüsünde, kelimeyi kişisel sözlüğe ekleme seçeneği vardır. Benzer bir yazım yanlışı kelimesini bir daha aradığınızda, kişisel sözlük kelimeleri, normal sözlüğe ek olarak öneriler listesinde görünecektir.  
Örneğin, kişisel sözlüğe "Fawaz" kelimesini eklerseniz, bir dahaki sefere "Fawz" yazdığınızda "Fawaz" gösterilen öneriler arasında bulunur.  
Kişisel sözlüğe eklenen herhangi bir kelimeyi, NVDA'nın kullanıcı yapılandırma klasöründeki yazım denetimi_dic klasöründe bulunan (dil etiketi) dosyasını (dil etiketi) düzenleyerek kaldırabilirsiniz.  
Bu, kurulu sürüm appdata/roaming/nvda ve taşınabilir sürüm kullanıcı yapılandırma klasörü içindir.  
ABD İngilizcesi için dosya adı en_US.dic olacaktır.  

### Bu defa yok say:  

Hata listesinde bulunan bir kelimeyi, öneri listesinin en sondan ikinci seçeneği olan "Bu defa yok say" seçeneğini kullanarak bu defalık bu şekilde kalmasını sağlayabilirsiniz.
örneğin: "merhaba nvda kullanıcıları, nvda ve eklentileriyle harika vakit geçireceğinizi umuyoruz. Şüphesiz, nvda harika bir ekran okuyucudur.", Metninde üç hata bulunur. Eğer NVDA kelimesi için "Bu defa yok Say" seçeneğini kullanırsak, Hata sayısı sıfıra düşecek ve hiç hata bulunmayacaktır.  

## Diğer diller için destek:

Eklenti, varsayılan olarak, eklentiyi yüklerken izninizle yüklenecek olan İngilizce sözlükle birlikte gelir.  
Yazım denetimi, varsayılan klavye giriş diline bağlı olarak yapılacaktır.  
Ancak, sözlük önceden yüklenmemişse, NVDA sizden o dilin sözlüğünü yüklemenizi isteyecektir.  
Evet'e tıkladığınızda, sözlük yüklenecek ve varsayılan klavye dilinde denetim yapılacaktır.  
Ek olarak, bir dili manuel olarak seçebileceğiniz ve daha önce indirilmemişse sözlüğü indirebileceğiniz veya o dilde yazım denetimi yapabileceğiniz dillerin listesini getirmek için NVDA+ALT+SHIFT+L tuşlarına basabilirsiniz.  
Varsayılan klavye diline dönmek için aynı kısa yol tuşlarına tekrar basabilirsiniz.  

### Sözlük yönetimi (Ayarlar)

Araçlar → Yazım Denetimi ayarları’ndan açın veya NVDA+Alt+Shift+S tuşlarına basın.

- Neler yapabilirsiniz?
	- Yüklü olmayan sözlükleri yükleyin.
	- Güncelleme varsa yüklü sözlükleri güncelleyin.
	- Artık gerek duymadığınız sözlükleri silin.
	- Listeyi filtreleyin: Tümü, Yüklü, Yüklü değil, Güncellemesi var.
	- Her dil için basit bir durum gösterilir: “Yüklü — Güncel — 7.0 MB”, “Yüklü — Güncelleme var — 7.0 MB” veya “Yüklü değil — 7.0 MB”.
- Notlar:
	- Güncelleme denetimleri arka planda çalışır; arayüz akıcı kalır.
	- Boyutlar MB cinsinden gösterilir.

## Notlar

- Escape tuşuna basarsanız, yapılan deyişiklikler kaydedilmeden pencereden çıkılacaktır.  
- Herhangi bir metni değiştirmeden sadece kişisel sözlüğe kelime eklemek isteseniz bile, bu kelimelerin kişisel sözlüğe eklenmesi için Control+R tuşlarına basmanız gerekir.  
- Yazım denetleme kısa yolu olan (NVDA+alt+s), Kaydetme kısayol tuşu (kontrol+r) ve manuel dil seçim kısayol tuşu olan (NVDA+Alt+SHIFT+L) seçeneklerini Girdi hreketleri iletişim kutusundan değiştirebilirsiniz.  


## Klavye kısayolları

- NVDA+alt+s: Eklentiyi etkinleştirir. (Giriş hareketlerinden değiştirilebilir).  
-Sağ ve Sol yön tuşları: Bulunan Yazım hataları arasında dolaşmamızı sağlar.  
- Enter veya Aşağı yön tuşu: Öneri listesini açar.  
- Yukarı ve aşağı yön tuşu: öneriler arasında gezinmemizi sağlar.  
- enter: üzerinde bulunan öneriyi seçer.  
- backspace: Seçilen bir öneriyi kaldırır.
- Ctrl+C: düzeltilmiş metni seçili metni değiştirmeden panoya kopyalamak için. (Giriş hareketlerinden değiştirilebilir).  
- Control+R: metin alanında seçilen önerileri değiştirmek için kullanılır. (Giriş hareketlerinden değiştirilebilir).  
- Control+Shift+P: odaktaki yanlış yazım veya öneriyi harf harf okur. (Giriş hareketlerinden değiştirilebilir).  
- Escape: Hem öneriler menüsünü hem de yanlış yazılmış sözcükler menüsünü kapatır.  
- NVDA+Alt+SHIFT+L: Farklı diller seçebileceğimiz bir liste açar. (giriş hareketlerinden değiştirilebilir).  
- NVDA+Alt+Shift+S: Yazım Denetimi ayarlarını açar (sözlük yönetimi).

## Kullanılan bileşenler ve sözlük kaynağı

- NVDA (NV Access): Eklenti NVDA içinde çalışır ve eklenti API’lerini kullanır.
- Arayüz: wxPython (NVDA’nın UI çerçevesi üzerinden).
- Yazım motoru: Enchant (PyEnchant) Hunspell arka ucuyla.
- Sözlükler: LibreOffice “dictionaries” deposundaki Hunspell sözlükleri.
	- Kaynak: https://github.com/LibreOffice/dictionaries
	- Kullanılan dosyalar: Her dil için .dic ve .aff çifti (ör. en_US.dic ve en_US.aff).
	- Lisans: Dile göre değişir; ayrıntılar için ilgili dil klasöründeki lisans dosyalarına bakın.
- Ağ: httpx (sözlük meta verileri ve dosyalarını almak için).
- Derleme sistemi: SCons (NVDA eklentisi derlemesi).

### Sözlüğü elle kurma

Elle bir sözlük kurmak isterseniz:

1) İlgili dil için .dic ve .aff dosyalarını yukarıdaki depodan indirin.
2) İki dosyayı da NVDA kullanıcı yapılandırma klasörüne kopyalayın:
	 - Kurulu NVDA: %APPDATA%\nvda\spellcheck_dictionaries\hunspell\
	 - Taşınabilir NVDA: userConfig\spellcheck_dictionaries\hunspell\
3) NVDA’yı yeniden başlatın. Dil, Yazım Denetimi ayarlarında “Yüklü” olarak görünür.

  