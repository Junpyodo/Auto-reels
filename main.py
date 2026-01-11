import os
import random
import re
import requests
import time
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

# 파일 경로 및 환경 변수 설정
TOPIC_FILE = "topics.txt"
EMERGENCY_FILE = "emergency_scripts.txt"
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

# --- [수정 구간] 해시태그 및 언급할 계정 설정 ---
HASHTAGS = """
#wealth #success #darkpsychology #motivation #millionaire 
#entrepreneur #luxurylifestyle #mindset #discipline
"""
MENTIONS = "@instagram @millionaire_mentor @successmindset @richkids"
# ----------------------------------------------

# 🚀 [성능/안정성 순서] AI 모델 리스트
AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

def post_to_instagram(video_url, caption):
    """인스타그램 Graph API를 사용하여 업로드 요청"""
    print(f"📤 인스타그램 서버에 영상 전달 중... URL: {video_url}")
    
    # 1. 미디어 컨테이너 생성
    post_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media"
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
            print(f"✅ 컨테이너 생성 완료 (ID: {creation_id})")
            
            # 2. 인스타그램 서버가 영상을 처리할 시간 대기 (최소 2분)
            print("⏳ 인스타그램 서버에서 영상 처리 중... 약 2분 대기합니다.")
            time.sleep(120) 
            
            # 3. 최종 게시물 발행
            publish_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media_publish"
            publish_payload = {
                'creation_id': creation_id,
                'access_token': ACCESS_TOKEN
            }
            r_pub = requests.post(publish_url, data=publish_payload)
            if 'id' in r_pub.json():
                print("🎉 인스타그램 업로드 최종 성공!")
            else:
                print(f"❌ 최종 발행 실패: {r_pub.text}")
        else:
            print(f"❌ 컨테이너 생성 실패: {res}")
    except Exception as e:
        print(f"❌ API 요청 중 에러 발생: {e}")

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
            time.sleep(2)
            response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
            new_list = [line.strip().replace('"', '') for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
            if new_list:
                final_scripts = list(set(scripts + new_list))
                with open(EMERGENCY_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(final_scripts))
                print(f"✅ 비상 대본 파일 업데이트 완료 ({model})")
                return
        except: continue

def get_best_sales_script(selected_topic):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    prompt_content = f"Topic: {selected_topic}\nCreate a powerful 20-word dark psychology script for an Instagram Reel. No intro."
    
    for model in AI_MODELS:
        for attempt in range(2):
            try:
                time.sleep(2)
                response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt_content}])
                script = response.choices[0].message.content.strip().replace('"', '')
                if script:
                    print(f"✅ AI 대본 생성 성공 (모델: {model})")
                    return script, False
            except:
                time.sleep(3)
                continue
    
    print("🆘 모든 AI 응답 없음. 비상 대본 파일에서 추출합니다.")
    e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep until the job is done."])
    chosen_e = random.choice(e_scripts)
    return chosen_e, True

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
                final_list = list(set(topics + new_topics))
                with open(TOPIC_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(final_list))
                print(f"✅ 주제 리스트 업데이트 완료 ({model})")
                return
        except: continue

def run_reels_bot():
    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth and power"])
    selected_topic = random.choice(topics)
    print(f"🎯 선택된 주제: {selected_topic}")
    
    script, is_emergency = get_best_sales_script(selected_topic)
    final_caption = f"{script}\n\n{MENTIONS}\n\n{HASHTAGS}"

    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 없음")
        return

    try:
        # 영상 편집 단계
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        txt = TextClip(
            script, fontsize=45, color='white', size=(video.w * 0.85, None),
            font='DejaVu-Sans-Bold', method='caption', align='center',
            interline=12, stroke_color='black', stroke_width=1.5
        ).set_duration(8).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final_video_path = "final_reels.mp4"
        final.write_videofile(final_video_path, fps=24, codec="libx264", audio=False)
        
        print(f"--- ★ 제작 완료 ★ ---")

        # 🚀 [업로드 단계] 멀티 서버를 활용한 임시 URL 생성
        public_url = None
        
        # 시도 1: 0x0.st
        try:
            print("🔗 임시 URL 생성 시도 1 (0x0.st)...")
            with open(final_video_path, 'rb') as f:
                r_file = requests.post("https://0x0.st", files={'file': f}, timeout=30)
                if r_file.status_code == 200:
                    public_url = r_file.text.strip()
        except Exception as e:
            print(f"⚠️ 0x0.st 시도 실패: {e}")

        # 시도 2: file.io (첫 번째 서버 실패 시)
        if not public_url:
            try:
                print("🔗 임시 URL 생성 시도 2 (file.io)...")
                with open(final_video_path, 'rb') as f:
                    r_file = requests.post("https://file.io", files={'file': f}, timeout=30)
                    if r_file.status_code == 200:
                        public_url = r_file.json().get('link')
            except Exception as e:
                print(f"⚠️ file.io 시도 실패: {e}")

        # 최종 업로드 실행
        if public_url:
            post_to_instagram(public_url, final_caption)
        else:
            print("❌ 모든 임시 URL 생성 서버가 응답하지 않습니다. 업로드를 건너뜁니다.")
        
        # 사용한 데이터 업데이트
        if is_emergency:
            update_emergency_scripts(script)
        else:
            update_topics_list(selected_topic)
            update_emergency_scripts()
            
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
