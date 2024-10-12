import sys
import os
import bs4
import requests
import zipfile
from pathlib import Path
import shutil

COOKIEPATH = "/root/.local/share/online-judge-tools/cookie.jar"

def load_lwp_cookies(cookie_path):
    """ LWP-Cookies-2.0形式のクッキーファイルを読み込み、辞書形式で返す """
    cookies = {}
    
    with open(cookie_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.startswith("Set-Cookie3:"):
            # クッキー情報をパース
            parts = line.split(" ")
            cookie_name_value = parts[1].split("=")
            cookie_name = cookie_name_value[0]
            cookie_value = cookie_name_value[1].strip().strip('""')
            cookies[cookie_name] = cookie_value
    
    return cookies

def main(url):
    # 前回のtoolsはけす
    shutil.rmtree(Path("tools").resolve(), ignore_errors=True)
    
    # セッションを作成
    session = requests.Session()

    # LWPクッキーをロードしてセッションに追加
    if os.path.exists(COOKIEPATH):
        cookies = load_lwp_cookies(COOKIEPATH)
        session.cookies.update(cookies)
        print(f"LWPクッキーをロードしました: {COOKIEPATH}")
    else:
        print(f"クッキーが見つかりません: {COOKIEPATH}")
        return
    
    # URLからHTMLを取得し、解析
    response = session.get(url)
    if response.status_code != 200:
        print(f"ページの取得に失敗しました (ステータスコード: {response.status_code})")
        return

    html = bs4.BeautifulSoup(response.text, 'html.parser')

    # タイトルを表示
    print(f"ページタイトル: {html.title.text}")
    
    # 「ローカル版」と書かれたリンクを探す
    link = html.find('a', text=lambda x: x and 'ローカル版' in x)
    if link is None:
        print("ローカル版リンクが見つかりませんでした。")
        return
    
    # リンクが相対パスの場合は、絶対パスに変換
    file_url = requests.compat.urljoin(url, link['href'])
    print(f"ローカル版のURL: {file_url}")


    # webvisのURLを取得
    link = html.find('a', text=lambda x: x and 'Web版' in x)
    if link is None:
        print("webvisリンクが見つかりませんでした。")
        return
    webvis_url = requests.compat.urljoin(url, link['href'])

    # ファイル名を取得
    file_name = os.path.basename(file_url)
    
    # ファイルをダウンロード
    response = session.get(file_url)
    if response.status_code == 200:
        with open(file_name, 'wb') as f:
            f.write(response.content)
        print(f"ファイルをダウンロードしました: {file_name}")

        # ZIPファイルを解凍する
        if file_name.endswith('.zip'):
            with zipfile.ZipFile(file_name, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(file_name))  # 同じディレクトリに解凍
            print(f"ファイルを解凍しました: {file_name}")

            # 元のZIPファイルを削除
            os.remove(file_name)
            print(f"元のZIPファイルを削除しました: {file_name}")
    else:
        print(f"ファイルのダウンロードに失敗しました (ステータスコード: {response.status_code})")
        
    # webvisのURLを保存
    with open("webvis_url.txt", "w") as f:
        f.write(webvis_url)
    return "tools", "webvis_url.txt"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python ahc_download_tools.py <url>')
        sys.exit(1)
    main(sys.argv[1])
