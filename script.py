import os
import requests
import sys
import warnings

# 1. Pillow کی وارننگز اور نئے ورژن کے بدلاؤ کو خودکار ہینڈل کرنے کا کوڈ
warnings.filterwarnings("ignore", category=DeprecationWarning)
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

# 2. ضروری لائبریریز کی امپورٹ
from moviepy.editor import VideoFileClip
from google import genai 

# کانفیگریشن اور سیٹنگز
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("BUFFER_WEBHOOK_URL")
VIDEOS_DIR = "videos"
HISTORY_FILE = "history.txt"

# جیمنائی کلائنٹ کی شروعات
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def get_history():
    """پہلے سے اپلوڈ شدہ ویڈیوز کی لسٹ پڑھنا"""
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r") as f:
        return set(line.strip() for line in f)

def add_to_history(filename):
    """نئی اپلوڈ ہونے والی ویڈیو کو ہسٹری میں لکھنا"""
    with open(HISTORY_FILE, "a") as f:
        f.write(filename + "\n")

def process_video_hd(input_path, output_path):
    """ویڈیو کو 720p پر سیٹ کرنا تاکہ سائز Make.com کی لمٹ (413 Error) کے اندر رہے"""
    clip = VideoFileClip(input_path)
    
    # کاپی رائٹ فٹ پرنٹ ختم کرنے کے لیے ہلکا سا زوم
    processed_clip = clip.fx(lambda c: c.resize(1.01))
    
    # 720p (720x1280) اور 800k بٹ ریٹ تاکہ سائز 5MB کے آس پاس رہے اور کوالٹی بھی اچھی ہو
    processed_clip.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac",
        bitrate="800k",
        preset="fast",   # فائل سائز کو کنٹرول میں رکھنے اور جلدی پروسیس کرنے کے لیے
        ffmpeg_params=["-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280"]
    )
    clip.close()
    processed_clip.close()

def generate_seo(topic_name):
    """جیمنائی کے ذریعے وائرل ایس ای او ڈیٹا بنانا (ایرر ہینڈلنگ کے ساتھ)"""
    default_seo = f"Title: {topic_name} 😱 | Viral Facts\n\nDescription: Amazing facts about {topic_name}. Subscribe for more!\n\nTags: #Shorts #Facts #Viral"
    
    if not client:
        return default_seo
        
    try:
        prompt = f"Create an engaging, viral title, a short description, and trending hashtags for a YouTube Short / TikTok video about: {topic_name}."
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ Gemini Error (Using Default SEO): {e}")
        return default_seo

def main():
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)
        print(f"📁 '{VIDEOS_DIR}' فولڈر بنا دیا گیا ہے۔")
        return

    history = get_history()
    files = [f for f in os.listdir(VIDEOS_DIR) if f.lower().endswith(('.mp4', '.mov'))]
    target_video = None
    
    # ایسی ویڈیو ڈھونڈنا جو ہسٹری میں نہ ہو
    for f in files:
        if f not in history:
            target_video = f
            break
            
    if not target_video:
        print("✅ تمام ویڈیوز اپلوڈ ہو چکی ہیں یا کوئی نئی ویڈیو نہیں ملی۔")
        return

    input_path = os.path.join(VIDEOS_DIR, target_video)
    output_path = os.path.join(VIDEOS_DIR, "processed_" + target_video)
    
    print(f"🎬 Processing Video (720p Optimised): {target_video}")
    try:
        process_video_hd(input_path, output_path)
    except Exception as e:
        print(f"❌ ویڈیو ایڈیٹنگ فیل ہو گئی: {e}")
        return
    
    print("🤖 Generating SEO with Gemini...")
    topic = os.path.splitext(target_video)[0]
    seo_text = generate_seo(topic)
    
    print("🚀 Sending to Make.com Webhook...")
    try:
        with open(output_path, 'rb') as f:
            files_dict = {"video_file": (target_video, f, "video/mp4")}
            data_dict = {"video_name": target_video, "seo_data": seo_text, "topic": topic}
            res = requests.post(MAKE_WEBHOOK_URL, data=data_dict, files=files_dict)
            
        if res.status_code in [200, 201]:
            print("🚀 Successfully uploaded to Make.com!")
            add_to_history(target_video)
            
            # کام مکمل ہونے پر فائلیں سرور سے ڈیلیٹ کرنا
            os.remove(input_path)
            os.remove(output_path)
            print("🗑️ Cleaned up: Both original and processed files deleted.")
        else:
            print(f"❌ Webhook Error! Code: {res.status_code}")
            if os.path.exists(output_path): 
                os.remove(output_path)
            
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        if os.path.exists(output_path): 
            os.remove(output_path)

if __name__ == "__main__":
    main()
