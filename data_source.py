import sys

import requests
from bs4 import BeautifulSoup
import configparser
import os
from urllib.parse import urlparse
from tqdm import tqdm
import shutil
from datetime import datetime

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
def get_cdda_latest(offset=0):
    global config
    global config_file
    print("正在查询最新版cdda……" if offset == 0 else f"正在查询前{offset}版cdda……")
    cdda_release_page = requests.get("https://github.com/CleverRaven/Cataclysm-DDA/tags")
    soup = BeautifulSoup(cdda_release_page.text, 'html.parser')
    a_link = soup.find_all('a', class_="Link--primary Link")
    last_release = {
        "label": a_link[offset].text,
        "href": ("https://github.com" + a_link[offset].get('href')).replace('tag', 'expanded_assets')
    }
    if last_release["label"] == config.get('Settings', 'cdda_version'):
        print(f"当前为符合设定的最新版本{last_release['label']}，无需更新。")
    else:
        print(f"发现新版本{last_release['label']}，即将开始更新。")
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
    target_link = soup.find(string=lambda text: search_text in text)
    if target_link is None:
        print("最新版本暂未发布您选择的系统版本。检查次新版本")
        get_cdda_latest(1)
        return
    download_url = (
            "https://github.com" +
            target_link.find_parent('a').get('href')
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
    # progress_bar = tqdm(total=file_size, unit='iB', unit_scale=True)
    progress_bar = tqdm(total=file_size, unit='iB', unit_scale=True, file=sys.stdout)
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


# 备份当前存档
def save_backup():
    # 检测存档是否存在
    save_exists = os.path.isdir(os.path.join('./CDDA', 'save'))
    if save_exists:
        print("检测到存档存在,开始备份。")
        # 检测备份文件夹是否存在，不存在则创建
        backup_folder_name = "SaveBackup"
        if not os.path.exists(backup_folder_name):
            os.makedirs(backup_folder_name)
        # 获取当前时间
        current_time = datetime.now()
        # 将时间格式化为 "yyyy-mm-dd-hh-mm-ss" 的形式
        formatted_time = current_time.strftime("%Y-%m-%d-%H:%M:%S")
        # 复制文件
        copy_directory_contents('./CDDA/save', f'./SaveBackup/{formatted_time}')
        print("存档备份完成！")
    else:
        print("未检测到存档。")


# 覆盖存档
def save_overwrite(src):
    # 要清空的目录路径
    directory = './CDDA/Save'
    # 检测存档是否存在
    # save_exists = os.path.isdir(os.path.join('./CDDA', 'save'))
    # if save_exists:
    #     print("检测到旧存档，正在清空存档文件夹……")
    #     # 删除目录下的所有内容
    #     for filename in os.listdir(directory):
    #         file_path = os.path.join(directory, filename)
    #         try:
    #             if os.path.isfile(file_path) or os.path.islink(file_path):
    #                 os.unlink(file_path)
    #             elif os.path.isdir(file_path):
    #                 shutil.rmtree(file_path)
    #         except Exception as e:
    #             print(f'清空目录失败. 原因: {e}')
    # else:
    #     os.makedirs('./CDDA/save', exist_ok=True)
    print("开始导入选择的存档……")
    copy_directory_contents(f'./SaveBackup/{src}', directory)
    print("存档导入完成！")


# 复制文件
def copy_directory_contents(src, dst):
    # 确保目标目录存在
    if not os.path.exists(dst):
        os.makedirs(dst)

    # 获取源目录中的文件列表，包括子目录中的文件
    files_to_copy = [os.path.join(dp, f) for dp, dn, filenames in os.walk(src) for f in filenames]
    total_files = len(files_to_copy)

    # 创建tqdm进度条
    with tqdm(total=total_files, unit='file', desc="复制文件") as pbar:
        for file in files_to_copy:
            # 构造源文件和目标文件的完整路径
            dst_file = os.path.join(dst, os.path.relpath(file, src))
            dst_dir = os.path.dirname(dst_file)

            # 确保目标文件的目录存在
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)

            # 复制文件
            shutil.copy2(file, dst_file)
            # 更新进度条
            pbar.update(1)
