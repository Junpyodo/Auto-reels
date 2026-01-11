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
    "google/gemini-2.0-flash-exp:free",      # 1순위: 최신 성능
    "google/gemini-flash-1.5-8b:free",       # 2순위: 높은 안정성
    "openai/gpt-4o-mini-2024-07-18:free",   # 3순위: 정확도
    "meta-llama/llama-3.1-8b-instruct:free"  # 4순위: 예비
]

def get_topics_from_file():
    if not os.path.exists(TOPIC_FILE):
        initial_topics = [
            "Dark psychology of wealth and power",
            "3 Habits of Self-Made Millionaires",
            "The 1% Wealth Checklist: Do you have these?"
        ]
        with open(TOPIC_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(initial_topics))
        return initial_topics
    
    with open(TOPIC_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def update_topics_list(used_topic):
    """AI가 새로운 주제 리스트를 생성 (실패 시 순차적 모델 전환)"""
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    topics = get_topics_from_file()
    if used_topic in topics:
        topics.remove(used_topic)

    print("🔄 AI가 새로운 주제 리스트를 생성 중입니다...")
    prompt = f"Based on these themes: {', '.join(topics[:5])}, generate 10 new, unique, and viral Instagram Reel topics about dark psychology, wealth, and success. Provide only a list of topics separated by newlines. No numbers, no intro."
    
    for model in AI_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            new_topics_str = response.choices[0].message.content.strip()
            new_topics = [line.strip() for line in new_topics_str.split('\n') if line.strip()]
            
            final_list = list(set(topics + new_topics))
            with open(TOPIC_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(final_list))
            print(f"✅ 주제 리스트 업데이트 완료 (사용 모델: {model})")
            return
        except Exception as e:
            print(f"⚠️ {model} 주제 생성 실패, 다음 순번 시도...")
            continue

def get_best_sales_script(selected_topic):
    """AI가 대본 생성 (실패 시 순차적 모델 전환)"""
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    prompt_content = f"""
    Topic: {selected_topic}
    Create a powerful psychological sales script for an Instagram Reel.
    Format: You can use a 3-line structure OR a bullet-point list (using '-' or '•').
    
    Constraints:
    - Language: English.
    - MAX 25 WORDS total.
    - Tone: Dark, Elite, Authoritative.
    - No intro/outro. Use actual newlines for spacing.
    """
    
    for model in AI_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_content}],
                temperature=0.9
            )
            script = response.choices[0].message.content.strip()
            script = script.replace('\\n', '\n').replace('"', '')
            print(f"✅ 대본 생성 성공 (사용 모델: {model})")
            return script
        except Exception as e:
            print(f"⚠️ {model} 대본 생성 실패, 다음 순번 시도...")
            continue
    return None

def run_reels_bot():
    topics = get_topics_from_file()
    if not topics:
        print("❌ 사용할 주제가 없습니다.")
        return

    selected_topic = random.choice(topics)
    print(f"🎯 선택된 주제: {selected_topic}")
    
    script = get_best_sales_script(selected_topic)
    
    if not script:
        print("❌ 모든 AI 모델의 요청이 거부되었습니다.")
        return

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
        
        print(f"--- ★ 제작 완료:{selected_topic} ★ ---")
        print(f"📝 최종 인스타그램 캡션 설정 완료:\n{final_caption}")
        
        update_topics_list(selected_topic)
        
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
