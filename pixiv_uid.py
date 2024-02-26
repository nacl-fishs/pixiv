import requests
import os
import time
import random
# 设置请求头和代理
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
    'Referer': 'https://www.pixiv.net/',
    'Cookie': '',   #f12找到你的cookie
}
proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}   #记得打开你的代理

# 获取用户输入的作者 UID
author_id = input("请输入作者的 UID: ")

# 获取作者的所有作品 PID
api_url = f"https://www.pixiv.net/ajax/user/{author_id}/profile/all"
response = requests.get(api_url, headers=headers, proxies=proxies)
data = response.json()
pids = data['body']['illusts'].keys()  # 获取所有作品的 PID

# 创建保存图片的目录
save_dir = "E:\\pixiv"
os.makedirs(save_dir, exist_ok=True)

# 在遍历 PID 之前初始化计数器
downloaded_images_count = 0

# 遍历 PID，访问每个作品的页面信息
for pid in pids:
    print(f"正在处理 PID: {pid}")

    pages_url = f"https://www.pixiv.net/ajax/illust/{pid}/pages"
    response = requests.get(pages_url, headers=headers, proxies=proxies)
    pages_data = response.json()

    for page in pages_data['body']:
        url = page['urls']['original']
        print(f"正在下载: {url}")
        response = requests.get(url, headers=headers, proxies=proxies, stream=True)
        if response.status_code == 200:
            file_name = os.path.basename(url)  # 从 URL 中提取文件名
            file_path = os.path.join(save_dir, file_name)  # 构造文件保存路径
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"图片已保存到 {file_path}")
            downloaded_images_count += 1  # 更新下载计数
        else:
            print(f"下载失败: {url}")

        # 随机等待 1-4 秒
        time.sleep(random.randint(1, 4))

print(f"已完成下载，共下载 {downloaded_images_count} 张图片。")
