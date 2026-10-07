import os
import json
from openai import OpenAI
import shutil
import sys
import os
from dotenv import load_dotenv

def get_files(folder):
    """拿到文件夹里的所有文件，不包含子文件夹"""
    files = []
    for name in os.listdir(folder):         # 列出文件夹里的所有东西
        path = os.path.join(folder, name)   # 拼出完整路径
        if os.path.isfile(path):            # 只要文件，跳过文件夹
            files.append(name)
    return files

load_dotenv()                        # 把 .env 读进来
key = os.getenv("DEEPSEEK_KEY")      # 摸出钥匙
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

def classify(files):
    """把一批文件名交给AI，返回{文件名: 类别}的字典"""

    # 把文件名拼成一段文本
    file_list = "\n".join(files)

    prompt = f"""你是一个文件整理助手。请根据下面的文件名，判断每个文件属于哪个类别。
    类别只能是：图片、文档、视频、音频、代码、压缩包、其他。
    
    严格按照以下JSON格式输出，不要输出任何其他内容：
    {{"文件名1": "类别", "文件名2": "类别"}}
    
    文件名列表：{file_list}"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":prompt}]
    )
    text = response.choices[0].message.content

    # 清理AI可能加的代码块标记
    text = text.strip().removeprefix("```json").removesuffix("```").strip()

    return json.loads(text)     # 转成Python字典

def organize(folder, mapping,dry_run = True):
    """按判断结果把文件移进对应子文件夹，dry_run = True时只打印计划，不动文件"""
    total = len(mapping)
    for i, (filename, category) in enumerate(mapping.items(),1):
        if dry_run:
            print(f"[预演]{filename}将移动到{category}/")
        else:
            src = os.path.join(folder, filename)

            if not os.path.exists(src):                         # 文件可能已经不存在了，跳过
                continue

            dst_dir = os.path.join(folder, category)
            os.makedirs(dst_dir,exist_ok=True)                  # 文件夹不存在就建，已存在也不报错

            shutil.move(src, os.path.join(dst_dir, filename))
            print(f"{filename}->{category}/")

            print(f"[{i}/{total}]处理完成")

if __name__ == "__main__":
    folder = r"C:\Users\suny_\Downloads"
    try:
        files = get_files(folder)
        if not files:
            print("这个文件夹里没有文件")
        else:
            print(f"发现{len(files)}个文件，正在交给AI分类……")
            mapping = classify(files)
            print("下面进行预演")
            organize(folder, mapping, True)
            org = input("预演完毕，需要按照预演结果整理吗(Y/N)？")
            if org == "Y" :
                organize(folder, mapping, False)
                print("整理完毕！")
            else:
                print("未整理，退出程序")
    except Exception as e:
        print(f"出错了：{e}")
        print("文件没有被移动，你放心")