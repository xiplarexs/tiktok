import sys
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description='TikTok Automation Bot')
    parser.add_argument('--mode', choices=['console', 'ui'], default='ui',
                      help='Run in console mode or with UI (default: ui)')
    parser.add_argument('--user-config', type=str, help='JSON dosyası yolu (kullanıcı bilgileri için)')
    parser.add_argument('--use-cookies', action='store_true', help='Mevcut cookieleri kullan')
    
    args = parser.parse_args()
    
    user_data = None
    if args.user_config:
        try:
            with open(args.user_config, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                print(f"Kullanıcı bilgileri yüklendi: {args.user_config}")
        except Exception as e:
            print(f"HATA: Kullanıcı bilgileri yüklenemedi: {str(e)}")
            sys.exit(1)
    
    if args.mode == 'console':
        from main import main as console_main
        console_main(user_data=user_data, use_cookies=args.use_cookies)
    else:
        from ui import main as ui_main
        ui_main(user_data=user_data, use_cookies=args.use_cookies)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"HATA: Beklenmedik bir sorun oluştu: {str(e)}")
        sys.exit(1)
