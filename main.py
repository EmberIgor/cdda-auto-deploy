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
        try:
            user_choose = int(input())
            if user_choose <= len(options):
                options[user_choose - 1].func()
                break
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
    directory_path = '/path/to/your/directory'
    folder_names = []
    for item in os.listdir(directory_path):
        # 检查当前项是否为目录
        if os.path.isdir(os.path.join(directory_path, item)):
            folder_names.append(item)
    print(folder_names)


if __name__ == '__main__':
    main_menu()
