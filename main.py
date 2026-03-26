from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import logging
import os
import json
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='tiktok_bot.log'
)

def setup_driver(use_cookies=False):
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Add proxy if needed
    # chrome_options.add_argument('--proxy-server=ip:port')
    
    # User data directory for cookies
    user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")
    if use_cookies:
        os.makedirs(user_data_dir, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        logging.info(f"Using Chrome profile at {user_data_dir}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Mask automation
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def load_cookies(driver, username):
    cookies_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies", f"{username}.pkl")
    if os.path.exists(cookies_file):
        try:
            driver.get("https://www.tiktok.com")
            cookies = pickle.load(open(cookies_file, "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
            logging.info(f"Cookies loaded for {username}")
            return True
        except Exception as e:
            logging.error(f"Error loading cookies for {username}: {e}")
    return False

def save_cookies(driver, username):
    try:
        cookies_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies")
        os.makedirs(cookies_dir, exist_ok=True)
        cookies_file = os.path.join(cookies_dir, f"{username}.pkl")
        pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))
        logging.info(f"Cookies saved for {username}")
        return True
    except Exception as e:
        logging.error(f"Error saving cookies: {e}")
        return False

def login_to_tiktok(driver, username, password, use_cookies=False):
    try:
        # Try using cookies first if requested
        if use_cookies and load_cookies(driver, username):
            driver.get("https://www.tiktok.com")
            time.sleep(5)
            # Check if login was successful by looking for elements that appear after login
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Following')] | //span[contains(text(), 'For You')]"))
                )
                logging.info("Successfully logged in using cookies")
                return True
            except:
                logging.warning("Login with cookies failed, will try with credentials")
        
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        logging.info("Navigating to TikTok login page...")
        time.sleep(random.uniform(3, 5))  # Wait for page to fully load
        
        # Check if we're already logged in
        if "login" not in driver.current_url:
            print("Zaten giriş yapılmış görünüyor...")
            logging.info("Already logged in, URL doesn't contain 'login'")
            return True
            
        # Find email/username input field and enter credentials
        try:
            username_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']"))
            )
            username_field.clear()
            # Type slowly like a human
            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            logging.info("Username entered")
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            logging.error(f"Could not find username field: {e}")
            username_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'email')]"))
            )
            username_field.clear()
            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))

        # Find password field and enter password
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_field.clear()
            # Type slowly like a human
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            logging.info("Password entered")
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            logging.error(f"Could not find password field: {e}")
            raise

        # Click login button
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@type, 'submit')] | //button[contains(text(), 'Log in')]"))
            )
            login_button.click()
            logging.info("Login button clicked")
        except Exception as e:
            logging.error(f"Could not find login button: {e}")
            raise

        # CAPTCHA check and wait for manual intervention
        print("If you see a CAPTCHA, please solve it manually...")
        logging.info("Waiting for potential CAPTCHA verification...")
        
        # Wait for user to handle CAPTCHA and login process to complete
        time.sleep(30)  
        
        # Check if login was successful using multiple methods
        success_indicators = [
            "//span[contains(text(), 'Following')]",
            "//span[contains(text(), 'For You')]",
            "//div[contains(@data-e2e, 'nav-login')]",
            "//div[contains(@class, 'user-info')]",
            "//div[contains(@data-e2e, 'profile-icon')]"
        ]
        
        for indicator in success_indicators:
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, indicator)))
                logging.info(f"Login success indicator found: {indicator}")
                
                # Save cookies for future use
                save_cookies(driver, username)
                return True
            except Exception as e:
                logging.debug(f"Indicator {indicator} not found: {str(e)[:100]}")
                continue
                
        # Check if we're not on login page anymore
        if "login" not in driver.current_url:
            logging.info("No longer on login page, assuming login successful")
            save_cookies(driver, username)
            return True
            
        # Check if we can access profile features
        try:
            driver.get("https://www.tiktok.com/foryou")
            time.sleep(5)
            if "login" not in driver.current_url:
                logging.info("Successfully navigated to For You page, login confirmed")
                save_cookies(driver, username)
                return True
        except:
            logging.warning("Failed to navigate to For You page")
        
        # We're still on login page, login failed
        logging.error("Still on login page or couldn't verify login, login failed")
        return False
            
    except Exception as e:
        logging.error(f"Login process failed with error: {e}")
        print(f"Login error: {e}")
        return False

def check_account_not_found(driver):
    """Profil bulunamadı hata mesajını kontrol eden fonksiyon"""
    error_texts = [
        "Bu hesap bulunamadı",
        "This account cannot be found", 
        "Couldn't find this account",
        "Account not found"
    ]
    
    try:
        # Sayfanın HTML içeriğini alarak kontrol edelim
        page_source = driver.page_source.lower()
        
        # Hata metinlerini kontrol et
        for text in error_texts:
            if text.lower() in page_source:
                return True
                
        # Hata mesajı içeren elementleri kontrol et
        error_elements = driver.find_elements(By.XPATH, 
            "//div[contains(text(), 'Bu hesap bulunamadı')] | " +
            "//div[contains(text(), 'account cannot be found')] | " + 
            "//div[contains(text(), 'find this account')] | " +
            "//h2[contains(text(), 'bulunamadı')]"
        )
        
        if error_elements and len(error_elements) > 0:
            return True
            
        # Check for empty profile indicators
        empty_profile = driver.find_elements(By.XPATH,
            "//div[contains(@class, 'error-page')] | " +
            "//div[contains(@class, 'error-container')]"
        )
        
        if empty_profile and len(empty_profile) > 0:
            return True
            
        return False
    except Exception as e:
        logging.error(f"Error checking for account not found: {e}")
        return False

def prompt_for_alternative_profile():
    """Kullanıcıdan alternatif profil URL'si ister"""
    print("\n" + "="*60)
    print("UYARI: Profil bulunamadı veya erişilemiyor.")
    print("Alternatif bir profil URL'si girebilirsiniz veya çıkmak için 'exit' yazabilirsiniz.")
    print("="*60)
    
    while True:
        new_url = input("\nLütfen geçerli bir TikTok profil URL'si girin (örn. https://www.tiktok.com/@gercekhesap)\n>> ")
        
        if new_url.lower() == 'exit':
            return None
        
        # URL formatını kontrol et
        if '@' in new_url and ('tiktok.com' in new_url or 'vm.tiktok.com' in new_url):
            return new_url
        else:
            print("Geçersiz URL format. Örnek: https://www.tiktok.com/@kullaniciadi")

def get_followers(driver, profile_url):
    driver.get(profile_url)
    time.sleep(random.uniform(4, 6))  # Daha uzun bekleme süresi
    followers = set()

    try:
        # İlk olarak profil bulunamadı hatası kontrolü yapalım
        if check_account_not_found(driver):
            print(f"HATA: Bu profil bulunamadı veya erişilemez: {profile_url}")
            logging.error(f"Account not found or not accessible: {profile_url}")
            return list(followers)
            
        # Önce profil sayfasındaki takipçi sayısını bulalım
        print("Profil sayfası yüklendi, takipçi butonunu arıyorum...")
        
        try:
            # Birden fazla olası seçici deneyelim
            followers_count = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//strong[contains(@data-e2e, 'followers')] | //strong[contains(@title, 'Followers')] | " +
                    "//div[contains(@data-e2e, 'followers-count')] | //span[contains(text(), 'Followers')]"
                ))
            )
            
            print(f"Takipçiler butonu bulundu: {followers_count.text}")
            
            # Takipçi sayısına tıklayalım
            driver.execute_script("arguments[0].click();", followers_count)
            print("Takipçi butonuna tıklandı, liste yükleniyor...")
            logging.info("Clicked followers button with JavaScript")
            
            # Modal pencere açılması için bekleyelim
            time.sleep(random.uniform(4, 6))
            
            # Modal pencere içinde takipçi listesini bulalım
            follower_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//div[contains(@class, 'modal')] | //div[@role='dialog'] | //div[contains(@class, 'share-layout')]"
                ))
            )
            print("Takipçi listesi modal penceresi bulundu.")
            
            # Takipçi listesini kaydıralım ve kullanıcı adlarını toplayalım
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 15  # Daha fazla takipçi almak için arttırıldı
            
            while scroll_count < max_scrolls:
                # Kullanıcı adlarını topla
                # TikTok'un farklı HTML yapılarını deneyerek kullanıcı adlarını alalım
                try:
                    usernames = follower_container.find_elements(By.XPATH, 
                        ".//span[contains(@data-e2e, 'username')] | " + 
                        ".//a[contains(@href, '/@')] | " +
                        ".//div[contains(@class, 'user-card')]//a | " +
                        ".//p[contains(@data-e2e, 'user-subtitle')] | " +
                        ".//div[contains(@data-e2e, 'user-info')]//a"
                    )
                    
                    for username_elem in usernames:
                        try:
                            username = username_elem.text.strip()
                            # @ işareti ekleyelim veya temizleyelim
                            if username and len(username) > 1:
                                clean_username = username.replace('@', '').strip()
                                if clean_username:
                                    followers.add(clean_username)
                        except:
                            continue
                    
                    if len(followers) > 0:
                        print(f"Şimdiye kadar {len(followers)} takipçi bulundu")
                except Exception as e:
                    print(f"Takipçi elementi bulunamadı: {str(e)[:100]}")
                
                # Modal içinde kaydırma yapmak için JavaScript kullanımı
                try:
                    # Scroll yaptığımız elemanı bul
                    scroll_element = follower_container.find_elements(By.XPATH, 
                        ".//div[contains(@class, 'scroll')] | .//div[contains(@class, 'list')] | .//div[@role='dialog']")
                    
                    if scroll_element and len(scroll_element) > 0:
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_element[0])
                    else:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                except:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                time.sleep(random.uniform(3, 4))  # Daha uzun bekleme süresi
                
                # Yeni yüksekliği kontrol et
                new_height = driver.execute_script("return document.body.scrollHeight")
                scroll_count += 1
                
                # Eğer yeterince takipçi topladıysak döngüyü kıralım
                if len(followers) >= 30:  # İstediğiniz takipçi sayısını ayarlayabilirsiniz
                    print(f"Yeterli takipçi toplandı: {len(followers)}")
                    break
                
                # Eğer sayfa sonuna geldiyse ve hiç takipçi bulunamadıysa
                if new_height == last_height and len(followers) == 0:
                    # Alternatif yöntemler deneyelim
                    print("Alternatif takipçi toplama yöntemi deneniyor...")
                    try:
                        # Doğrudan profil URL'sinden takipçileri almayı deneyelim
                        driver.get(f"{profile_url}/followers")
                        time.sleep(random.uniform(3, 5))
                        
                        # Sayfa içindeki tüm kullanıcı adları bağlantılarını alalım
                        all_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/@')]")
                        for link in all_links:
                            try:
                                username = link.get_attribute("href").split("/@")[-1].split("?")[0]
                                if username:
                                    followers.add(username)
                            except:
                                continue
                    except Exception as e:
                        print(f"Alternatif yöntem başarısız: {str(e)[:100]}")
                
                last_height = new_height
            
            print(f"Toplam {len(followers)} takipçi bulundu.")
            
        except Exception as e:
            print(f"Takipçi butonunu bulamadım, hata: {str(e)[:200]}")
            logging.error(f"Could not find followers button: {str(e)[:200]}")
            
            # Eğer takipçi butonu bulunamazsa doğrudan HTML'den bağlantıları toplamayı deneyelim
            print("HTML'den bağlantıları toplamayı deniyorum...")
            all_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/@')]")
            for link in all_links:
                try:
                    username = link.get_attribute("href").split("/@")[-1].split("?")[0]
                    if username:
                        followers.add(username)
                except:
                    continue
            
            print(f"HTML'den {len(followers)} potansiyel takipçi bulundu.")
            
    except Exception as e:
        print(f"Takipçi alımı genel hatası: {str(e)[:200]}")
        logging.error(f"Error while fetching followers: {str(e)[:200]}")
    
    # Takipçi listesi boşsa, manuel test listesi kullanabiliriz
    if not followers:
        print("Takipçi bulunamadı, test listesi kullanılıyor...")
        # Test için birkaç kullanıcı adı ekleyin
        test_users = ["user1", "user2", "user3"]
        return test_users
    
    return list(followers)

def get_messageable_users(driver, followers):
    messageable_users = []
    print(f"{len(followers)} takipçinin mesaj özelliği kontrol ediliyor...")
    
    # İlerlemeyi göstermek için sayaç
    counter = 0
    total = len(followers)
    
    for user in followers:
        counter += 1
        print(f"Kullanıcı kontrol ediliyor [{counter}/{total}]: {user}")
        
        try:
            username = user.strip('@')
            driver.get(f"https://www.tiktok.com/@{username}")
            time.sleep(random.uniform(2, 3))
            
            # Hesap bulunamadı kontrolü
            if check_account_not_found(driver):
                print(f"HATA: {username} hesabı bulunamadı veya erişilemez.")
                logging.warning(f"Account not found or not accessible: {username}")
                continue
                
            try:
                # Profil yüklendi mi kontrol edilir
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2, .user-info, [data-e2e='user-title']"))
                )
                print(f"{username} profili yüklendi.")
                
                # Farklı mesaj butonlarını kontrol edelim
                message_button_xpath = (
                    "//button[contains(text(), 'Message')] | "
                    "//button[contains(@class, 'message') or contains(@class, 'Message')] | "
                    "//div[contains(@data-e2e, 'message-icon')] | "
                    "//button[contains(@aria-label, 'Send message')] | "
                    "//a[contains(@href, '/message')]"
                )
                
                # Mesaj butonunu önce görünür mü diye kontrol edelim
                try:
                    message_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, message_button_xpath))
                    )
                    
                    # Butonun görünür ve etkin olduğunu kontrol et
                    if message_button.is_displayed():
                        print(f"{username} için mesaj butonu görünür.")
                        
                        # JavaScript ile tıklanabilirliği kontrol et
                        is_clickable = driver.execute_script(
                            "return arguments[0].offsetParent !== null && "
                            "!arguments[0].disabled && "
                            "arguments[0].style.display !== 'none' && "
                            "arguments[0].style.visibility !== 'hidden'", 
                            message_button
                        )
                        
                        if is_clickable:
                            messageable_users.append(username)
                            print(f"{username} mesaj gönderilebilir.")
                            logging.info(f"{username} is messageable.")
                        else:
                            print(f"{username} için mesaj butonu görünür ama tıklanabilir değil.")
                    else:
                        print(f"{username} için mesaj butonu görünür değil.")
                except Exception as e:
                    print(f"{username} için mesaj butonu bulunamadı: {str(e)[:100]}")
                    continue
                
            except Exception as e:
                print(f"{username} profili yüklenemedi: {str(e)[:100]}")
                continue
                
        except Exception as e:
            print(f"{user} profil sayfası açılamadı: {str(e)[:100]}")
            continue
            
    print(f"Toplam {len(messageable_users)} mesaj gönderilebilir kullanıcı bulundu.")
    return messageable_users

def send_message(driver, user, message):
    try:
        driver.get(f"https://www.tiktok.com/@{user}")
        time.sleep(random.uniform(3, 5))  # Daha uzun bekleme
        
        # Hesap bulunamadı kontrolü
        if check_account_not_found(driver):
            print(f"HATA: {user} hesabı bulunamadı veya erişilemez, mesaj gönderimi atlanıyor.")
            logging.warning(f"Account not found or not accessible, skipping message: {user}")
            return False
            
        # Farklı CSS seçiciler deneyerek mesaj butonunu bul
        message_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//button[contains(text(), 'Message')] | //div[contains(@data-e2e, 'message-icon')] | //button[contains(@aria-label, 'Send message')]"
            ))
        )
        logging.info(f"Found message button for {user}")
        
        # Butonu tıklamadan önce JavaScript ile görünürlük ve tıklanabilirlik kontrolü
        is_clickable = driver.execute_script(
            "return arguments[0].offsetParent !== null && !arguments[0].disabled && arguments[0].style.display !== 'none' && arguments[0].style.visibility !== 'hidden'", 
            message_button
        )
        
        if is_clickable:
            # JavaScript kullanarak tıklama
            driver.execute_script("arguments[0].click();", message_button)
            logging.info(f"Clicked message button for {user} using JS")
        else:
            # Normal tıklama dene
            message_button.click()
            logging.info(f"Clicked message button for {user} using Selenium")
            
        time.sleep(random.uniform(3, 5))  # Mesaj paneli açılması için bekle
        
        # Mesaj alanını bul (farklı seçiciler deneyerek)
        message_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//textarea | //div[@contenteditable='true'] | //input[@placeholder='Send a message...']"
            ))
        )
        
        # Alanın odaklanabilir olduğundan emin ol
        driver.execute_script("arguments[0].focus();", message_field)
        time.sleep(random.uniform(0.5, 1))
        
        # Mesajı insan gibi yaz
        for char in message:
            message_field.send_keys(char)
            time.sleep(random.uniform(0.1, 0.2))
        
        logging.info(f"Message typed for {user}")
        time.sleep(random.uniform(1, 2))
        
        # Enter tuşu ile gönder
        message_field.send_keys(Keys.RETURN)
        
        # Alternatif olarak gönder butonunu arayıp tıklamayı dene
        try:
            send_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[@aria-label='Send message'] | //button[contains(@data-e2e, 'send-button')]"
                ))
            )
            send_button.click()
            logging.info(f"Send button clicked for {user}")
        except:
            logging.info(f"No send button found, used Enter key for {user}")
        
        time.sleep(random.uniform(2, 3))  # Mesajın gönderilmesi için bekle
        print(f"{user}'a mesaj gönderildi.")
        logging.info(f"Message sent to {user}.")
        
        return True  # Mesaj başarıyla gönderildi
    except Exception as e:
        print(f"{user}'a mesaj gönderilemedi: {str(e)[:200]}")
        logging.error(f"Failed to send message to {user}: {str(e)[:200]}")
        return False

def main(use_cookies=True):
    # Tek kullanıcı için bilgiler
    username = "kullaniciadi"  # TikTok kullanıcı adınız 
    password = "sifre"  # TikTok şifreniz
    profile_url = "https://www.tiktok.com/@hedefhesap"  # Takipçileri alınacak hesap
    message = "Merhaba! Bu bir test mesajıdır."  # Gönderilecek mesaj
    
    # Yapılandırma dosyasından yükle (varsa)
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                username = config.get("username", username)
                password = config.get("password", password)
                profile_url = config.get("profile_url", profile_url)
                message = config.get("message", message)
                logging.info("Config loaded from config.json")
    except Exception as e:
        logging.error(f"Error loading config.json: {e}")

    try:
        driver = setup_driver(use_cookies)
        print(f"İşlem başlatılıyor: {username}")
        logging.info(f"İşlem başlatılıyor: {username}")
        
        login_success = login_to_tiktok(driver, username, password, use_cookies)
        
        if not login_success:
            print(f"Giriş başarısız: {username}, işlem durduruluyor...")
            logging.error(f"Login failed for {username}, terminating")
            driver.quit()
            return
        
        print("Giriş başarılı! Takipçiler alınıyor...")
        
        profile_attempt = 0
        max_profile_attempts = 3
        current_profile_url = profile_url
        
        while profile_attempt < max_profile_attempts:
            try:
                # Profil URL'sini kontrol et
                driver.get(current_profile_url)
                time.sleep(random.uniform(3, 5))
                
                # Profil bulunamadı kontrolü
                if check_account_not_found(driver):
                    print(f"HATA: Bu profil bulunamadı veya erişilemez: {current_profile_url}")
                    logging.warning(f"Profile not found or not accessible: {current_profile_url}")
                    
                    # Alternatif profil URL'si iste
                    new_profile_url = prompt_for_alternative_profile()
                    
                    if not new_profile_url:
                        print("İşlem kullanıcı tarafından iptal edildi.")
                        logging.info("Operation canceled by user")
                        return
                    
                    current_profile_url = new_profile_url
                    profile_attempt += 1
                    print(f"Yeni profil deneniyor: {current_profile_url}")
                    continue
                
                # Profil geçerliyse takipçileri al
                followers = get_followers(driver, current_profile_url)
                print(f"{len(followers)} takipçi bulundu.")
                logging.info(f"Found {len(followers)} followers")
                
                if not followers:
                    print("Takipçi bulunamadı. Başka bir profil denemek ister misiniz?")
                    new_profile_url = prompt_for_alternative_profile()
                    
                    if not new_profile_url:
                        print("İşlem kullanıcı tarafından iptal edildi.")
                        return
                    
                    current_profile_url = new_profile_url
                    profile_attempt += 1
                    continue
                
                # Takipçiler başarıyla alındıysa döngüden çık
                break
                
            except Exception as e:
                print(f"Profil işleme hatası: {str(e)[:200]}")
                logging.error(f"Profile processing error: {e}")
                
                # Alternatif profil URL'si iste
                new_profile_url = prompt_for_alternative_profile()
                
                if not new_profile_url:
                    print("İşlem kullanıcı tarafından iptal edildi.")
                    return
                
                current_profile_url = new_profile_url
                profile_attempt += 1
        
        # Maksimum deneme sayısına ulaşıldıysa
        if profile_attempt >= max_profile_attempts and not followers:
            print(f"Maksimum deneme sayısına ({max_profile_attempts}) ulaşıldı. İşlem durduruluyor...")
            logging.warning(f"Maximum profile attempts ({max_profile_attempts}) reached, terminating")
            return
        
        print("Mesaj gönderilebilir kullanıcılar bulunuyor...")
        messageable_users = get_messageable_users(driver, followers)
        print(f"{len(messageable_users)} mesaj gönderilebilir kullanıcı bulundu.")
        logging.info(f"Found {len(messageable_users)} messageable users")
        
        if not messageable_users:
            print("Mesaj gönderilebilir kullanıcı bulunamadı, işlem durduruluyor...")
            logging.warning("No messageable users found, terminating")
            driver.quit()
            return
        
        print("Mesajlar gönderiliyor...")
        for user in messageable_users:
            send_message(driver, user, message)
            print(f"{user}'a mesaj gönderildi. Bir sonraki için bekleniyor...")
            # TikTok sunucularını yormamak için daha uzun bekleme
            time.sleep(random.uniform(45, 90))  
            
        print("Mesaj gönderme işlemi tamamlandı.")
        logging.info("Message sending completed")
                
    except Exception as e:
        print(f"İşlem sırasında hata oluştu: {e}")
        logging.error(f"Error during operation: {e}")
    
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
        logging.critical(f"Critical error in main process: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
            logging.info("WebDriver closed")

if __name__ == "__main__":
    try:
        main(use_cookies=True)
    except Exception as e:
        print(f"HATA: Beklenmedik bir sorun oluştu: {e}")
        logging.critical(f"Application crashed: {e}")