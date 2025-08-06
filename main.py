from flask import Flask, jsonify, send_from_directory, abort, request, session
from datetime import datetime
import time
import os
import threading
import json
import dotenv
from utils import logging,notify_discord_webhook, compress_to_webp_lqip_batch,batch_generate_thumbnails
from werkzeug.utils import secure_filename

dotenv.load_dotenv()
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# log設定
logging.basicConfig(level=logging.WARNING, filename='server.log', filemode='w', format='%(asctime)s - %(levelname)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.getLogger('werkzeug').setLevel(logging.WARNING)

UPLOAD_FOLDER_IMAGES = os.path.join('static', 'photos')
UPLOAD_FOLDER_VIDEOS = os.path.join('static', 'videos')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','raw'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_VIDEOS, exist_ok=True)

# 輔助函數：檢查檔案是否為允許的類型
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 輔助函數：更新 travel_data.json 文件
def update_travel_data(prefecture_key, file_type, filenames):
    data_filepath = os.path.join('data', 'travel_data.json')
    try:
        # 載入現有的旅行資料
        with open(data_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 檢查縣市是否存在
        if prefecture_key not in data:
            return False, f"[錯誤] 在旅行資料中未找到「{prefecture_key}」。"

        # 根據檔案類型更新對應的列表
        if file_type == 'image':
            if 'photos' not in data[prefecture_key]:
                data[prefecture_key]['photos'] = []
            # 僅添加新的檔案名，避免重複
            for filename in filenames:
                if filename not in data[prefecture_key]['photos']:
                    data[prefecture_key]['photos'].append(filename)
        elif file_type == 'video':
            if 'videos' not in data[prefecture_key]:
                data[prefecture_key]['videos'] = []
            # 僅添加新的檔案名，避免重複
            for filename in filenames:
                if filename not in data[prefecture_key]['videos']:
                    data[prefecture_key]['videos'].append(filename)
        else:
            return False, "Invalid file type specified."

        # 將更新後的資料寫回文件
        with open(data_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True, "[消息] 數據更新成功。"
    except FileNotFoundError:
        return False, "[錯誤] 未找到 travel_data.json。請確保它存在於“data”目錄中。"
    except json.JSONDecodeError:
        return False, "[錯誤] travel_data.json 中的 JSON 格式無效。請檢查其內容。"
    except Exception as e:
        return False, f"[錯誤] 更新旅行資料時發生意外錯誤：{str(e)}"
    
# 輔助函數：背景排程任務
def background_compressor():
    while True:
        compress_to_webp_lqip_batch(UPLOAD_FOLDER_IMAGES)
        batch_generate_thumbnails(UPLOAD_FOLDER_VIDEOS)
        time.sleep(3600)  # 每小時執行一次

# 輔助函數：啟動背景線程
def start_background_thread():
    thread = threading.Thread(target=background_compressor)
    thread.daemon = True  # 隨主程式退出
    thread.start()

# 網站縮圖
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# 錯誤處理：剔除機器人並導向 410 頁面
@app.errorhandler(404)
def page_not_found(e):
    return send_from_directory('static', 'error.html'), 410

@app.errorhandler(403)
def page_forbidden(e):
    return send_from_directory('static', 'error.html'), 410

@app.errorhandler(410)
def page_gone(e):
    return send_from_directory('static', 'error.html'), 410

@app.before_request
def block_bots():
    ua = request.headers.get('User-Agent', '')
    if 'bot' in ua.lower() or 'spider' in ua.lower():
        abort(403)

@app.route('/robots.txt')
def robots_txt():
    txt = """
User-agent: *
Disallow: /
"""
    return txt

# 解鎖時間 API
@app.route('/api/unlock-time')
def unlock_time():
    return jsonify({
        "unlockTime": "2025-07-26T00:00:00Z"
    })

# 旅遊資料 API
@app.route('/api/travel-data')
def travel_data():
    try:
        with open(os.path.join('data', 'travel_data.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "[錯誤] 未找到 travel_data.json"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "[錯誤] JSON 格式無效"}), 500

# 圖片上傳 API
@app.route('/api/upload/image', methods=['POST'])
def upload_image():
    if 'prefecture' not in request.form:
        return jsonify({"error": "[錯誤] 未指定區域"}), 400
    
    # 檢查是否有檔案在請求中
    if 'images' not in request.files:
        return jsonify({"error": "[錯誤] 沒有選取檔案"}), 400

    prefecture = request.form['prefecture']
    files = request.files.getlist('images') # 獲取所有名為 'images' 的檔案
    uploaded_filenames = []

    for file in files:
        if file.filename == '':
            continue # 跳過空的檔案欄位
        
        # 檢查檔案類型是否允許
        if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            filename = session['current_user'] + '_' + secure_filename(file.filename) # 安全處理檔名
            filepath = os.path.join(UPLOAD_FOLDER_IMAGES, filename)
            try:
                file.save(filepath) # 儲存檔案
                uploaded_filenames.append(filename)
            except Exception as e:
                notify_discord_webhook(f"[錯誤] 將圖片 {filename} 儲存到 {filepath} 時發生錯誤：{str(e)}")
                return jsonify({"error": f"[錯誤] 將圖片 {filename} 儲存到 {filepath} 時發生錯誤：{str(e)}"}), 500
        else:
            return jsonify({"error": f"[錯誤] 檔案“{file.filename}”類型不允許或無效。"}), 400

    if not uploaded_filenames:
        return jsonify({"error": "[錯誤] 未上傳有效的圖像檔案。"}), 400

    # 更新 travel_data.json
    success, message = update_travel_data(prefecture, 'image', uploaded_filenames)
    if success:
        notify_discord_webhook(f"[成功] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {session['current_user']}已上傳至{prefecture} 的圖片：{', '.join(uploaded_filenames)}")
        return jsonify({"message": "圖片上傳成功", "filenames": uploaded_filenames}), 200
    else:
        notify_discord_webhook(f"[錯誤] 更新圖片的旅遊數據時出錯：{message}")
        return jsonify({"error": message}), 500

# 新增：影片上傳 API
@app.route('/api/upload/video', methods=['POST'])
def upload_video():
    if 'prefecture' not in request.form:
        return jsonify({"error": "未指定區域"}), 400
    
    # 檢查是否有檔案在請求中
    if 'videos' not in request.files:
        return jsonify({"error": "[錯誤] 沒有選取檔案"}), 400

    prefecture = request.form['prefecture']
    files = request.files.getlist('videos') # 獲取所有名為 'videos' 的檔案
    uploaded_filenames = []

    for file in files:
        if file.filename == '':
            continue # 跳過空的檔案欄位
        
        # 檢查檔案類型是否允許
        if file and allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
            filename = session['current_user'] + '_' + secure_filename(file.filename) # 安全處理檔名
            filepath = os.path.join(UPLOAD_FOLDER_VIDEOS, filename)
            try:
                file.save(filepath) # 儲存檔案
                uploaded_filenames.append(filename)
            except Exception as e:
                notify_discord_webhook(f"[錯誤] 將影片 {filename} 儲存到 {filepath} 時發生錯誤：{str(e)}")
                return jsonify({"error": f"[錯誤] 將圖片 {filename} 儲存到 {filepath} 時發生錯誤：{str(e)}"}), 500
        else:
            return jsonify({"error": f"[錯誤] 檔案“{file.filename}”類型不允許或無效。"}), 400

    if not uploaded_filenames:
        return jsonify({"error": "[錯誤] 未上傳有效的圖像檔案。"}), 400

    # 更新 travel_data.json
    success, message = update_travel_data(prefecture, 'video', uploaded_filenames)
    if success:
        notify_discord_webhook(f"[成功] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {session['current_user']}已上傳至{prefecture} 的影片: {', '.join(uploaded_filenames)}")
        return jsonify({"message": "影片上傳成功", "filenames": uploaded_filenames}), 200
    else:
        notify_discord_webhook(f"更新影片的旅遊數據時出錯：{message}")
        return jsonify({"error": message}), 500

# 首頁路由
@app.route('/japan/<user>')
def index(user):
    # 載入用戶資料
    user_data_path = os.path.join('data', 'user.json')
    try:
        with open(user_data_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
            current_user = users.get(user, None)
    except FileNotFoundError:
        print(f"[錯誤] 在 {user_data_path} 處找不到 user.json")
        return send_from_directory('static', 'error.html'), 410
    except json.JSONDecodeError:
        print(f"[錯誤] {user_data_path} 處的 user.json 中的 JSON 格式無效")
        return send_from_directory('static', 'error.html'), 410

    if not current_user:
        return send_from_directory('static', 'error.html'), 410
    
    # 發送 Discord 通知
    notify_discord_webhook(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {current_user}進入了網站!")
    logging.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {current_user}進入了網站!")
    session['current_user'] = current_user
    # 返回主頁 HTML
    return send_from_directory('static', 'japan.html')

# 啟動伺服器
if __name__ == "__main__":
    context = (
        os.getenv('fullchain'),
        os.getenv('privkey')
    )
    start_background_thread()
    app.run(host="0.0.0.0", port=443, ssl_context=context, debug= True)

