import os
import requests
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

def process_video(input_path, output_path):
    """فٹ پرنٹس ختم کرنے اور کاپی رائٹ سے بچنے کے لیے ویڈیو پروسیسنگ"""
    clip = VideoFileClip(input_path)
    # ہلکا سا زوم (1.01) تاکہ فٹ پرنٹ بدلے، ٹیکسٹ سیدھا رہے اور آواز آگے پیچھے نہ ہو
    processed_clip = clip.fx(lambda c: c.resize(1.01))
    processed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    clip.close()
    processed_clip.close()

def generate_seo(topic_name):
    """جیمنائی کے ذریعے وائرل ایس ای او ڈیٹا بنانا"""
    if not client:
        return f"Title: {topic_name} 😱 | Viral Facts\n\nDescription: Amazing facts about {topic_name}. Subscribe for more!\n\nTags: #Shorts #Facts #Viral"
    
    try:
        prompt = f"Create an engaging, viral title, a short description, and trending hashtags for a YouTube Short / TikTok video about: {topic_name}. Keep it clean and optimized for SEO."
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"⚠️ Gemini SEO Error: {e}")
        return f"Title: {topic_name} 😱 | Viral Facts\n\nDescription: Amazing facts about {topic_name}. Subscribe for more!\n\nTags: #Shorts #Facts #Viral"

def main():
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)
        print(f"📁 '{VIDEOS_DIR}' کا فولڈر بنا دیا گیا ہے۔ اس میں ویڈیوز رکھیں۔")
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
    
    print(f"🎬 Processing Video: {target_video}")
    try:
        process_video(input_path, output_path)
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
            print("🚀 Make.com پر کامیابی سے اپلوڈ ہو گیا!")
            add_to_history(target_video)
            
            # فائلیں ڈیلیٹ کرنے کا عمل (کلین اپ)
            os.remove(input_path)
            os.remove(output_path)
            print(f"🗑️ Cleaned up: original and processed files for {target_video} deleted.")
        else:
            print(f"❌ Webhook Error! Status code: {res.status_code}")
            if os.path.exists(output_path):
                os.remove(output_path)
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == "__main__":
    main()
