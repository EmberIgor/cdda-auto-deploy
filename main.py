import data_source
import os


# 主菜单
def main_menu():
    class OptionsItems:
        def __init__(self, label, func):
            self.label = label
            self.func = func

    options = [
        OptionsItems("检查并更新版本", update_cdda),
        OptionsItems("存档备份", save_buckup),
        OptionsItems("存档读取", save_overwrite),
    ]
    while True:
        options_index = 0
        for options_item in options:
            print(f"{options_index + 1}. {options_item.label}")
            options_index += 1
        print(f"{options_index + 1}. 退出")
        try:
            user_choose = int(input())
            if user_choose <= len(options) + 1:
                if user_choose == len(options) + 1:
                    break
                os.system('cls')
                options[user_choose - 1].func()
            else:
                print("超出选择范围")
        except ValueError:
            print("请输入合法字符")


def update_cdda():
    data_source.find_config()
    data_source.get_cdda_latest()


def save_buckup():
    data_source.save_backup()


def save_overwrite():
    # 获取备份的存档列表
    directory_path = './SaveBackup'
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    folder_names = []
    for item in os.listdir(directory_path):
        # 检查当前项是否为目录
        if os.path.isdir(os.path.join(directory_path, item)):
            folder_names.append(item)
    folder_index = 0
    for folder in folder_names:
        print(f'{folder_index + 1}. {folder}')
        folder_index += 1
    print(f'{folder_index + 1}. 返回')
    try:
        user_choose = int(input())
        if user_choose <= len(folder_names) + 1:
            if user_choose == len(folder_names) + 1:
                return
            data_source.save_overwrite(folder_names[user_choose - 1])
        else:
            print("超出选择范围")
    except ValueError:
        print("请输入合法字符")


if __name__ == '__main__':
    main_menu()
