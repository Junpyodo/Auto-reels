import os
import random
import re
import requests
import time
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

# --- [설정 확인] ---
GITHUB_ID = "Junpyodo"        
REPO_NAME = "Auto-reels"      
# -----------------------

TOPIC_FILE = "topics.txt"
EMERGENCY_FILE = "emergency_scripts.txt"
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

HASHTAGS = "#wealth #success #darkpsychology #motivation #millionaire #mindset"
MENTIONS = "@instagram"

AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

def get_list_from_file(file_path, default_values):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(default_values))
        return default_values
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def update_emergency_scripts(used_script=None):
    scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence.", "Success is the best revenge."])
    if used_script and used_script in scripts:
        scripts.remove(used_script)
    print("🔄 AI가 비상용 대본 리스트를 보충 중입니다...")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    prompt = "Generate 10 powerful, viral 20-word dark psychology scripts for Instagram Reels. One per line. No numbers."
    for model in AI_MODELS:
        try:
            time.sleep(5) # AI 에러 방지용 딜레이
            response = client.chat.completions.create(
                model=model, 
                messages=[{"role": "user", "content": prompt}],
                extra_headers={"HTTP-Referer": "https://github.com"}
            )
            new_list = [line.strip().replace('"', '') for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
            if new_list:
                final_scripts = list(set(scripts + new_list))
                with open(EMERGENCY_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(final_scripts))
                print(f"✅ 비상 대본 업데이트 완료 ({model})")
                return
        except: continue

def update_topics_list(used_topic):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    topics = get_list_from_file(TOPIC_FILE, ["Wealth psychology"])
    if used_topic in topics: topics.remove(used_topic)
    print("🔄 AI가 새로운 주제 리스트를 생성 중입니다...")
    prompt = f"Based on {used_topic}, generate 10 new Instagram Reel topics about dark psychology and wealth. Newlines only."
    for model in AI_MODELS:
        try:
            response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
            new_topics = [line.strip() for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
            if new_topics:
                with open(TOPIC_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(list(set(topics + new_topics))))
                print(f"✅ 주제 리스트 업데이트 완료 ({model})")
                return
        except: continue

def get_best_sales_script(selected_topic):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    prompt_content = f"Topic: {selected_topic}\nCreate a powerful 20-word dark psychology script for an Instagram Reel. No intro."
    for model in AI_MODELS:
        try:
            print(f"🤖 {model} 모델에게 대본 요청 중...")
            time.sleep(5)
            response = client.chat.completions.create(
                model=model, 
                messages=[{"role": "user", "content": prompt_content}],
                extra_headers={"HTTP-Referer": "https://github.com"}
            )
            script = response.choices[0].message.content.strip().replace('"', '')
            if script: return script, False
        except: continue
    e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep until the job is done."])
    return random.choice(e_scripts), True

def post_to_instagram(video_url, caption):
    """최신 인스타그램 릴스 전용 API 방식 적용"""
    print(f"📤 인스타그램 릴스 업로드 시도 중...")
    post_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media"
    
    # 릴스 업로드에 최적화된 데이터 구조
    payload = {
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    
    try:
        r = requests.post(post_url, data=payload)
        res = r.json()
        if 'id' in res:
            creation_id = res['id']
            print(f"✅ 컨테이너 생성 성공 (ID: {creation_id}) \n⏳ 인스타그램 서버에서 처리 중... (3분 대기)")
            time.sleep(180) # 릴스는 처리 시간이 길어 3분이 안전합니다.
            
            publish_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media_publish"
            r_pub = requests.post(publish_url, data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN})
            if 'id' in r_pub.json():
                print("🎉 🎉 인스타그램 릴스 최종 업로드 성공! 🎉 🎉")
            else:
                print(f"❌ 최종 발행 실패: {r_pub.text}")
        else:
            print(f"❌ 컨테이너 생성 실패: {res}")
    except Exception as e:
        print(f"❌ API 에러 발생: {e}")

def run_reels_bot():
    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth and power"])
    selected_topic = random.choice(topics)
    print(f"🎯 주제: {selected_topic}")
    
    script, is_emergency = get_best_sales_script(selected_topic)
    final_caption = f"{script}\n\n{MENTIONS}\n\n{HASHTAGS}"

    if not os.path.exists("background.mp4"): return

    try:
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        txt = TextClip(script, fontsize=45, color='white', size=(video.w * 0.85, None),
                       font='DejaVu-Sans-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final_video_name = "reels_video.mp4"
        final.write_videofile(final_video_name, fps=24, codec="libx264", audio=False)
        
        # GitHub Pages 주소 생성
        public_url = f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{final_video_name}"
        post_to_instagram(public_url, final_caption)
        
        # 데이터 업데이트 로직
        if is_emergency:
            update_emergency_scripts(used_script=script)
        else:
            update_topics_list(used_topic=selected_topic)
            update_emergency_scripts()
            
    except Exception as e:
        print(f"❌ 작업 도중 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
