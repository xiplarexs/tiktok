import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
from main import setup_driver, login_to_tiktok, get_followers, get_messageable_users, send_message
import time
import random

class KullaniciArayuzu:
    def __init__(self, master, title):
        self.master = master
        self.master.title(title)
        self.master.geometry("800x600")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='tiktok_bot.log'
        )
        
        self.create_widgets()
        self.driver = None
        self.is_running = False
    
    def create_widgets(self):
        # Account credentials frame
        account_frame = ttk.LabelFrame(self.master, text="Hesap Bilgileri")
        account_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(account_frame, text="Kullanıcı Adı:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.username_entry = ttk.Entry(account_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(account_frame, text="Şifre:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.password_entry = ttk.Entry(account_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(account_frame, text="Profil URL:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.profile_url_entry = ttk.Entry(account_frame, width=50)
        self.profile_url_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Message frame
        message_frame = ttk.LabelFrame(self.master, text="Mesaj")
        message_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(message_frame, text="Gönderilecek Mesaj:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.message_text = scrolledtext.ScrolledText(message_frame, width=50, height=5)
        self.message_text.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Control frame
        control_frame = ttk.Frame(self.master)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Başlat", command=self.start_process)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Durdur", command=self.stop_process, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(self.master, text="Log")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.config(state="disabled")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        logging.info(message)
    
    def start_process(self):
        if not self.username_entry.get() or not self.password_entry.get() or not self.profile_url_entry.get():
            messagebox.showerror("Hata", "Lütfen tüm hesap bilgilerini doldurun!")
            return
        
        if not self.message_text.get("1.0", "end-1c").strip():
            messagebox.showerror("Hata", "Lütfen bir mesaj girin!")
            return
        
        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        # Start the process in a separate thread
        threading.Thread(target=self.run_bot, daemon=True).start()
    
    def stop_process(self):
        self.is_running = False
        self.log("İşlem durdurma talebi alındı...")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def run_bot(self):
        try:
            self.log("Driver başlatılıyor...")
            self.driver = setup_driver()
            
            username = self.username_entry.get()
            password = self.password_entry.get()
            profile_url = self.profile_url_entry.get()
            message = self.message_text.get("1.0", "end-1c")
            
            self.log(f"TikTok'a giriş yapılıyor: {username}")
            login_success = login_to_tiktok(self.driver, username, password)
            
            if not login_success:
                self.log("Giriş başarısız oldu!")
                messagebox.showerror("Hata", "TikTok girişi başarısız oldu!")
                self.stop_process()
                return
            
            self.log("Giriş başarılı!")
            
            if not self.is_running:
                return
            
            self.log("Takipçiler alınıyor...")
            followers = get_followers(self.driver, profile_url)
            self.log(f"Toplam {len(followers)} takipçi bulundu.")
            
            if not self.is_running:
                return
            
            self.log("Mesaj gönderilebilir kullanıcılar kontrol ediliyor...")
            messageable_users = get_messageable_users(self.driver, followers)
            self.log(f"Mesaj gönderilebilir {len(messageable_users)} kullanıcı bulundu.")
            
            for i, user in enumerate(messageable_users):
                if not self.is_running:
                    self.log("İşlem kullanıcı tarafından durduruldu.")
                    break
                
                self.log(f"[{i+1}/{len(messageable_users)}] {user}'a mesaj gönderiliyor...")
                send_message(self.driver, user, message)
                
                # Sleep to avoid rate limiting
                sleep_time = random.uniform(30, 60)
                self.log(f"Bir sonraki mesaj için {sleep_time:.1f} saniye bekleniyor...")
                time.sleep(sleep_time)
            
            self.log("İşlem tamamlandı!")
            messagebox.showinfo("Bilgi", "Mesaj gönderme işlemi tamamlandı!")
            
        except Exception as e:
            self.log(f"Hata oluştu: {e}")
            messagebox.showerror("Hata", f"İşlem sırasında bir hata oluştu: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.stop_process()

def main():
    root = tk.Tk()
    app = KullaniciArayuzu(root, "TikTok Mesajlaşma Botu")
    root.mainloop()

if __name__ == "__main__":
    main()
