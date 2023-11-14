import requests
from bs4 import BeautifulSoup
import configparser
import os
import re

config_file = 'config.ini'
config = configparser.ConfigParser()


# 检查是否有配置文件
def find_config():
    global config
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        config.add_section('Settings')
        config.set('Settings', 'cdda_version', '0.0')
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print(f"没有找到配置文件，已创建新的配置文件{config_file}。")
    else:
        config.read(config_file)
        # cdda_version = config.get('Settings', 'cdda_version')


# 获取cdda最新发行版
def get_cdda_latest():
    global config
    global config_file
    cdda_release_page = requests.get("https://github.com/CleverRaven/Cataclysm-DDA/tags")
    soup = BeautifulSoup(cdda_release_page.text, 'html.parser')
    a_link = soup.find('a', class_="Link--primary Link")
    last_release = {
        "label": a_link.text,
        "href": ("https://github.com" + a_link.get('href')).replace('tag', 'expanded_assets')
    }
    if last_release["label"] == config.get('Settings', 'cdda_version'):
        print(f"当前为最新版本{last_release["label"]}，无需更新")
    else:
        folder_name = "CDDA"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        download_cdda(last_release["href"])


# 下载最新cdda文件
def download_cdda(page_url):
    print(page_url)
    res = requests.get(page_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    search_text = "cdda-windows-tiles-sounds-x64"
    download_url = soup.find_all(string=lambda text: search_text in text)[0].parent
    print(download_url)

