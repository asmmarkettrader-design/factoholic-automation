import os
import requests
import sys

# Pillow کا ورژن ایرر فکس کرنے کے لیے شارٹ کٹ
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from moviepy.editor import VideoFileClip

# کانفیگریشن اور سیٹنگز
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("BUFFER_WEBHOOK_URL")
VIDEOS_DIR = "videos"
HISTORY_FILE = "history.txt"

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def get_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r") as f:
        return set(line.strip() for line in f)

def add_to_history(filename):
    with open(HISTORY_FILE, "a") as f:
        f.write(filename + "\n")

def process_video_hd(input_path, output_path):
    """ویڈیو کو 1080p پر اپ گریڈ کرنا، کوالٹی بڑھانا اور سائز 10MB سے کم رکھنا"""
    clip = VideoFileClip(input_path)
    
    # کاپی رائٹ فٹ پرنٹ ختم کرنے کے لیے ہلکا سا زوم
    processed_clip = clip.fx(lambda c: c.resize(1.01))
    
    # ویڈیو کی لمبائی دیکھ کر بٹ ریٹ سیٹ کرنا تاکہ سائز 10MB سے کم رہے
    duration = clip.duration
    # اگر شارٹ ویڈیو ہے (مثلاً 30-50 سیکنڈ)، تو 1500k بٹ ریٹ 10MB سے بہت کم سائز بنائے گا لیکن کوالٹی 1080p رہے گی
    target_bitrate = "1500k" 
    
    # ویڈیو کو 1080p (یا 720p اگر ویڈیو اصل میں بہت چھوٹی ہو) رزلٹ میں سیو کرنا
    processed_clip.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac",
        bitrate=target_bitrate,
        preset="slow", # یہ کوالٹی کو مزید بہتر (Enhance) کرتا ہے
        ffmpeg_params=["-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"] # 1080p Vertical Short
    )
    clip.close()
    processed_clip.close()

def generate_seo(topic_name):
    if not client:
        return f"Title: {topic_name} 😱 | Viral Facts\n\nDescription: Amazing facts about {topic_name}. Subscribe for more!\n\nTags: #Shorts #Facts #Viral"
    try:
        prompt = f"Create an engaging, viral title, a short description, and trending hashtags for a YouTube Short / TikTok video about: {topic_name}."
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text
    except Exception as e:
        return f"Title: {topic_name} 😱 | Viral Facts\n\nDescription: Amazing facts about {topic_name}. Subscribe for more!\n\nTags: #Shorts #Facts #Viral"

def main():
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)
        return

    history = get_history()
    files = [f for f in os.listdir(VIDEOS_DIR) if f.lower().endswith(('.mp4', '.mov'))]
    target_video = None
    
    for f in files:
        if f not in history:
            target_video = f
            break
            
    if not target_video:
        print("✅ تمام ویڈیوز اپلوڈ ہو چکی ہیں۔")
        return

    input_path = os.path.join(VIDEOS_DIR, target_video)
    output_path = os.path.join(VIDEOS_DIR, "processed_" + target_video)
    
    print(f"🎬 Processing HD Video & Enhancing: {target_video}")
    try:
        process_video_hd(input_path, output_path)
    except Exception as e:
        print(f"❌ ویڈیو ایڈیٹنگ فیل ہو گئی: {e}")
        return
    
    topic = os.path.splitext(target_video)[0]
    seo_text = generate_seo(topic)
    
    print("🚀 Sending to Make.com...")
    try:
        with open(output_path, 'rb') as f:
            files_dict = {"video_file": (target_video, f, "video/mp4")}
            data_dict = {"video_name": target_video, "seo_data": seo_text, "topic": topic}
            res = requests.post(MAKE_WEBHOOK_URL, data=data_dict, files=files_dict)
            
        if res.status_code in [200, 201]:
            print("🚀 Successfully uploaded!")
            add_to_history(target_video)
            os.remove(input_path)
            os.remove(output_path)
        else:
            print(f"❌ Webhook Error! Code: {res.status_code}")
            if os.path.exists(output_path): os.remove(output_path)
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        if os.path.exists(output_path): os.remove(output_path)

if __name__ == "__main__":
    main()
