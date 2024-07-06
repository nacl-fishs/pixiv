import requests
import time
import random
import os
import re
import json

# 清理文件名中的非法字符
def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# 加载已下载图片的记录
def load_downloaded_records(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 保存已下载图片的记录
def save_downloaded_records(file_path, records):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

# 设置请求头和代理，需要自己填入cookie
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.pixiv.net/',
    'Cookie': ''
}
proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

# 用户输入页数范围
start_page = int(input("请输入开始页数: "))
end_page = int(input("请输入结束页数: "))

# 初始化一个空列表来收集所有页的 PIDs
all_pids = []

# 遍历用户指定的页数范围
for page in range(start_page, end_page + 1):
    follow_latest_url = f"https://www.pixiv.net/ajax/follow_latest/illust?p={page}&mode=all&lang=zh"
    response = requests.get(follow_latest_url, headers=headers, proxies=proxies)

    if response.status_code == 200:
        data = response.json()
        pids = data['body']['page']['ids']
        print(f"第 {page} 页的 PIDs: {pids}")
        all_pids.extend(pids)  # 将当前页的 PIDs 添加到总列表中
    else:
        print(f"获取第 {page} 页数据失败，状态码：{response.status_code}")

# 创建保存图片的目录
save_dir = "H:\\pixiv\\update"
os.makedirs(save_dir, exist_ok=True)

# 加载已下载图片的记录
records_file = "downloaded_records.json"
downloaded_records = load_downloaded_records(records_file)

# 在遍历 PID 之前初始化计数器
downloaded_images_count = 0

# 遍历 PID，访问每个作品的页面信息
for pid in all_pids:
    print(f"Processing PID: {pid}")

    # 检查是否已下载过
    if str(pid) in downloaded_records:
        print(f"PID {pid} 已存在记录中，跳过下载。")
        continue

    illust_info_url = f"https://www.pixiv.net/ajax/illust/{pid}"
    response = requests.get(illust_info_url, headers=headers, proxies=proxies)
    illust_info_data = response.json()['body']

    # 从作品信息中提取作者 UID
    author_uid = illust_info_data['tags']['authorId']

    # 安全地提取第一个标签的 userName，确保标签列表不为空
    if illust_info_data['tags']['tags']:
        author_userName = illust_info_data['tags']['tags'][0].get('userName', '未知作者')
    else:
        author_userName = '未知作者'

    title = illust_info_data['title']

    tags = []
    for tag in illust_info_data['tags']['tags']:
        # 初始化标签字符串，先添加 "#" 和原始标签
        tag_str = "#" + tag['tag']
        # 检查是否存在翻译
        if 'translation' in tag and 'en' in tag['translation']:
            # 如果存在，添加翻译的英文内容
            tag_str += " (" + tag['translation']['en'] + ")"
        tags.append(tag_str)

    r18 = any(tag['tag'] == 'R-18' for tag in illust_info_data['tags']['tags'])
    if illust_info_data['tags']['tags']:
        userName = illust_info_data['tags']['tags'][0].get('userName', 'Unknown')
    else:
        userName = 'Unknown'

    pages_url = f"https://www.pixiv.net/ajax/illust/{pid}/pages"
    response = requests.get(pages_url, headers=headers, proxies=proxies)
    pages_data = response.json()

    for page in pages_data['body']:
        url = page['urls']['original']
        file_name = os.path.basename(url)
        file_path = os.path.join(save_dir, file_name)

        # 检查文件是否已存在
        if os.path.exists(file_path):
            print(f"文件 {file_path} 已存在，跳过下载。")
            continue

        print(f"Downloading: {url}")
        response = requests.get(url, headers=headers, proxies=proxies, stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"已保存到 {file_path}")

            # 保存到作者文件夹
            author_userName_cleaned = clean_filename(author_userName)  # 清理作者用户名
            author_dir = os.path.join("H:\\pixiv", author_userName_cleaned)
            os.makedirs(author_dir, exist_ok=True)
            new_path = os.path.join(author_dir, file_name)
            with open(new_path, 'wb') as f:
                f.write(open(file_path, 'rb').read())
            print(f"已保存到 {new_path}")

            downloaded_images_count += 1
            print(f"已成功下载第 {downloaded_images_count} 张图片")

            # 记录已下载的图片信息
            downloaded_records[str(pid)] = {
                'pid': pid,
                'uid': author_uid,
                'title': title,
                'r18': r18,
                'tags': tags,
                'userName': author_userName,
                'width': page['width'],
                'height': page['height'],
                'file_path': file_path,
                'new_path': new_path,
                'url': url
            }

            # 保存记录到 JSON 文件
            save_downloaded_records(records_file, downloaded_records)

        else:
            print(f"Failed to download {url}")

        # 随机等待 1-4 秒
        time.sleep(random.randint(1, 4))
