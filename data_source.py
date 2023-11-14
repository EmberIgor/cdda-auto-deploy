import requests
from bs4 import BeautifulSoup
import configparser
import os
from urllib.parse import urlparse
from tqdm import tqdm
import shutil

config_file = 'config.ini'
config = configparser.ConfigParser()


# 检查是否有配置文件
def find_config():
    global config
    print("正在读取配置文件……")
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        config.add_section('Settings')
        config.set('Settings', 'cdda_version', '0.0')
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print(f"没有找到配置文件，已创建新的配置文件{config_file}。")
    else:
        config.read(config_file)


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
        print(f"当前为最新版本{last_release['label']}，无需更新")
    else:
        folder_name = "CDDA"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        download_cdda(last_release["href"], last_release["label"])


# 下载最新cdda文件
def download_cdda(page_url, label):
    # 获取下载链接和文件名
    res = requests.get(page_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    search_text = "cdda-windows-tiles-sounds-x64"
    download_url = (
            "https://github.com" +
            soup.find_all(string=lambda text: search_text in text)[0].find_parent('a').get('href')
    )
    parsed_url = urlparse(download_url)
    file_name = os.path.basename(parsed_url.path)
    # 发送HEAD请求获取文件大小
    response = requests.head(download_url)
    file_size = int(response.headers.get('content-length', 0))
    # 设置块大小
    block_size = 1024
    response = requests.get(download_url, stream=True)
    # 创建进度条
    progress_bar = tqdm(total=file_size, unit='iB', unit_scale=True)
    # 写入文件
    with open(file_name, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
        progress_bar.close()
    # 解压文件
    print("正在解压文件……请不要关闭窗口")
    shutil.unpack_archive(file_name, 'CDDA')
    # 解压完成后删除原文件
    os.remove(file_name)
    # 更新config中记录的版本信息
    config.set('Settings', 'cdda_version', label)
    with open(config_file, 'w') as configfile:
        config.write(configfile)
