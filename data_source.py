import requests
from bs4 import BeautifulSoup
import configparser
import os
from urllib.parse import urlparse
from tqdm import tqdm
import shutil
from datetime import datetime
import zipfile
import re

config_file = 'config.ini'
config = configparser.ConfigParser()
game_dir = 'CDDA'


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
    global game_dir
    print("正在查询最新版cdda……")
    last_file_info = get_download_url(
        "https://github.com/CleverRaven/Cataclysm-DDA/tags",
        "cdda-windows-tiles-x64" if os.path.isdir(game_dir) else "cdda-windows-tiles-sounds-x64"
    )
    if last_file_info:
        pattern = r"\d{4}-\d{2}-\d{2}-\d{4}"
        new_build_number = re.search(pattern, last_file_info['tag_name']).group(0)
        if os.path.exists(game_dir):
            with open(f'{game_dir}/VERSION.txt', 'r') as file:
                content = file.readlines()
            build_number_line = None
            for line in content:
                if 'build number' in line.lower():
                    build_number_line = line.strip()
                    break
            old_build_number = build_number_line.split(':', 1)[1].strip()
            if new_build_number == old_build_number:
                print(f"当前游戏已经是最新版本{old_build_number}，无需更新。")
                return
        print(f"发现新版本{new_build_number}，即将开始更新。")
        download_and_extract_release_file(last_file_info['file_name'], last_file_info['download_url'], game_dir)
        print("更新完成。")


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
        # 将时间格式化为 "yyyy-mm-dd-hh.mm.ss" 的形式
        formatted_time = current_time.strftime("%Y-%m-%d-%H.%M.%S")
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
    save_exists = os.path.isdir(os.path.join('./CDDA', 'save'))
    if save_exists:
        print("检测到旧存档，正在清空存档文件夹……")
        # 递归地获取所有文件
        all_files = get_all_files(directory)
        # 使用tqdm显示进度条，进度条以文件数量为单位
        for file_path in tqdm(all_files, desc="清空进度", unit="file"):
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'清空目录失败. 原因: {e}')
    else:
        os.makedirs('./CDDA/save', exist_ok=True)
    # 导入存档
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


# 获取指定git url的发行版信息
def get_git_last_release_info(release_url):
    pattern = r'github\.com\/([^\/]+\/[^\/]+)'
    match = re.search(pattern, release_url)
    release_page = requests.get(release_url)
    soup = BeautifulSoup(release_page.text, 'html.parser')
    a_links = soup.find_all('a', class_="Link--primary Link")

    release_info = {
        "repository_name": match.group(1) if match else None,
        "last_tag_names": [a_item.text for a_item in a_links]
    }
    return release_info


# 获取指定仓库发行版的某个文件信息
def get_git_release_file_info(repository_name, release_tag_name, search_text):
    res = requests.get(f"https://github.com/{repository_name}/releases/expanded_assets/{release_tag_name}")
    soup = BeautifulSoup(res.text, 'html.parser')
    target_link = soup.find(string=lambda text: search_text in text)
    if target_link is None:
        return False
    download_url = (
            "https://github.com" +
            target_link.find_parent('a').get('href')
    )
    parsed_url = urlparse(download_url)
    file_name = os.path.basename(parsed_url.path)
    return {
        "file_name": file_name,
        "download_url": download_url
    }


# 根据仓库和文件名获取download_url和文件名
def get_download_url(release_url, search_text):
    release_info = get_git_last_release_info(release_url)
    last_file_info = False
    for tag_name in release_info["last_tag_names"]:
        last_file_info = get_git_release_file_info(
            release_info["repository_name"],
            tag_name,
            search_text
        )
        if last_file_info:
            last_file_info["tag_name"] = tag_name
            break
    if last_file_info:
        return last_file_info
    else:
        return False


# 下载文件并解压到指定目录
def download_and_extract_release_file(file_name, download_url, extract_dir):
    # 发送HEAD请求获取文件大小
    response_get = requests.get(download_url, stream=True)
    file_size = int(response_get.headers.get('content-length', 0))
    response_get.close()
    # 设置块大小
    block_size = 1024
    # 创建进度条
    progress_bar = tqdm(total=file_size if file_size > 0 else None, unit='iB', unit_scale=True, desc="下载进度")
    # 使用GET请求下载文件
    with requests.get(download_url, stream=True) as response:
        with open(file_name, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
    # 解压文件
    # 压缩文件的路径
    zip_path = file_name
    # 确保路径存在
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    # 打开压缩文件
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # 获取所有文件的列表
        file_list = zip_ref.infolist()
        # 创建tqdm进度条
        with tqdm(total=len(file_list), unit='file', desc=f"正在解压") as progress_bar:
            for file in file_list:
                # 解压单个文件
                zip_ref.extract(file, extract_dir)
                # 更新进度条
                progress_bar.update(1)
    # 解压完成后删除原文件
    os.remove(file_name)


def get_all_files(directory):
    """递归地获取目录中所有文件的路径"""
    all_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_files
