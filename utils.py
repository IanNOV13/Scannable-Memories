import os
import logging
import requests
from PIL import Image, ImageFilter, ImageOps
from moviepy import VideoFileClip
import io

# --- 通知相關 ---
def notify_discord_webhook(message, webhook_url=None):
    """通過 Discord Webhook 發送消息或圖片。"""
    if webhook_url is None:
        webhook_url = os.getenv("DISCORD_WEBHOOK")
    if not webhook_url:
        #print("[通知] Discord Webhook URL 未設置，跳過通知。")
        logging.error("[通知] Discord Webhook URL 未設置，跳過通知。")
        return

    try:
        headers = {"Content-Type": "application/json"}
        data = {"content": message, "username": "網站登入資訊"}
        #res = requests.post(webhook_url, headers=headers, json=data)
    except requests.exceptions.RequestException as e:
        #print(f"[錯誤] 發送 Discord 通知失敗: {e}")
        logging.error(f"[錯誤] 發送 Discord 通知失敗: {e}")
    except Exception as e:
        #print(f"[錯誤] Discord 通知過程中發生未知錯誤: {e}")
        logging.error(f"[錯誤] Discord 通知過程中發生未知錯誤: {e}")


def extract_first_frame_as_webp(video_path, output_path, max_width=800):
    try:
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(0)  # 取首幀
        img = Image.fromarray(frame)

        # 縮圖（等比例）
        if img.width > max_width:
            height = int((max_width / img.width) * img.height)
            img = img.resize((max_width, height), Image.LANCZOS)

        # 儲存為 WebP
        img.save(output_path, format='WEBP', quality=80, method=6)
        clip.close()

        #print(f"生成縮圖：{output_path}")
    except Exception as e:
        #print(f"無法處理 {video_path}：{e}")
        logging.error(f"無法處理 {video_path}：{e}")


def batch_generate_thumbnails(input_dir="static/videos", output_dir="static/videos/lowres"):
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
            continue

        input_path = os.path.join(input_dir, filename)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.webp")

        # 跳過已存在縮圖
        if os.path.exists(output_path):
            #print(f"已存在，略過：{output_path}")
            logging.info(f"已存在，略過：{output_path}")
            continue

        extract_first_frame_as_webp(input_path, output_path)

def compress_to_webp_lqip_batch(input_dir, max_size_kb=1024, scale=0.1):
    output_dir = os.path.join(input_dir, "lowres")
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp",'.raw')):
            continue

        name, _ = os.path.splitext(filename)
        output_filename = f"{name}.webp"
        output_path = os.path.join(output_dir, output_filename)

        # 若已存在就跳過
        if os.path.exists(output_path):
            #print(f"已存在：{output_filename}，略過")
            logging.info(f"已存在：{output_filename}，略過")
            continue

        input_path = os.path.join(input_dir, filename)
        img = Image.open(input_path)
        img = ImageOps.exif_transpose(img).convert("RGB")  # 加入自動旋轉處理

        # 縮小 + 模糊
        small = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.BILINEAR
        )
        blurred = small.resize(img.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))

        quality = 60
        while quality >= 10:
            buffer = io.BytesIO()
            blurred.save(buffer, format="WEBP", quality=quality, method=6)
            size_kb = buffer.tell() / 1024

            if size_kb <= max_size_kb:
                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                #print(f"✅ 儲存 {output_filename} - {size_kb:.2f}KB (quality={quality})")
                break

            quality -= 5
        else:
            blurred.save(buffer, format="WEBP", quality=quality, method=6)
            #print(f"⚠️ 無法壓縮 {filename} 至 10KB 以下")
            logging.info(f"⚠️ 無法壓縮 {filename} 至 10KB 以下")

if __name__ == "__main__":
    #compress_to_webp_lqip_batch(os.path.join('static', 'photos'))
    batch_generate_thumbnails()