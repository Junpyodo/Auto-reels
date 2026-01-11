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
EMERGENCY_FILE = "emergency_scripts.txt" # 비상 대본 저장 파일
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

def get_list_from_file(file_path, default_values):
    """파일에서 리스트를 읽어오고, 파일이 없으면 기본값으로 생성"""
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(default_values))
        return default_values
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def update_emergency_scripts(used_script=None):
    """비상 대본 파일에서 사용한 것을 지우고 AI에게 새 목록을 받아 보충"""
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
    """AI 대본 생성 시도, 실패 시 비상 대본 파일에서 추출"""
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    prompt_content = f"Topic: {selected_topic}\nCreate a powerful 20-word dark psychology script for an Instagram Reel. No intro."
    
    # 1. AI 모델 순차 시도
    for model in AI_MODELS:
        for attempt in range(2): # 모델당 2번 시도
            try:
                time.sleep(2)
                response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt_content}])
                script = response.choices[0].message.content.strip().replace('"', '')
                if script:
                    print(f"✅ AI 대본 생성 성공 (모델: {model})")
                    return script, False # (대본, 비상여부)
            except:
                time.sleep(3)
                continue
    
    # 2. 모든 AI 실패 시 파일에서 비상 대본 사용
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
                with open(TOPIC_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(list(set(topics + new_topics))))
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
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        txt = TextClip(
            script, fontsize=45, color='white', size=(video.w * 0.85, None),
            font='DejaVu-Sans-Bold', method='caption', align='center',
            interline=12, stroke_color='black', stroke_width=1.5
        ).set_duration(8).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio=False)
        
        print(f"--- ★ 제작 완료 ★ ---")
        
        # 사용한 데이터 업데이트
        if is_emergency:
            update_emergency_scripts(script) # 사용한 비상 대본 삭제 및 보충
        else:
            update_topics_list(selected_topic) # 일반 주제 업데이트
            update_emergency_scripts() # (선택사항) 평소에도 비상 대본 보충
            
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
