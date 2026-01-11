import os
import random
import re
import requests
import time
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import moviepy.video.fx.all as vfx

# --- [필수 설정 항목] ---
GITHUB_ID = "Junpyodo"        # 스크린샷에 나온 아이디로 설정함
REPO_NAME = "Auto-reels"      # 스크린샷에 나온 저장소 이름으로 설정함
# -----------------------

TOPIC_FILE = "topics.txt"
EMERGENCY_FILE = "emergency_scripts.txt"
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

HASHTAGS = "#wealth #success #darkpsychology #motivation #millionaire #mindset"
MENTIONS = "@instagram"

# 모델 리스트 최적화 (Gemini 위주로 안정화)
AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

def post_to_instagram(video_url, caption):
    """최신 인스타그램 릴스 업로드 방식 (v19.0) 적용"""
    print(f"📤 인스타그램 릴스 업로드 시도 중... \n🔗 URL: {video_url}")
    
    # 1. 미디어 컨테이너 생성 (REELS 전용 파라미터 적용)
    post_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media"
    payload = {
        'media_type': 'REELS', # 반드시 REELS로 명시
        'video_url': video_url,
        'caption': caption,
        'share_to_feed': 'true', # 피드에도 공유
        'access_token': ACCESS_TOKEN
    }
    
    try:
        r = requests.post(post_url, data=payload)
        res = r.json()
        
        if 'id' in res:
            creation_id = res['id']
            print(f"✅ 미디어 컨테이너 생성 성공! (ID: {creation_id})")
            
            # 2. 인스타그램 서버 처리 대기 (릴스는 용량이 커서 3분 권장)
            print("⏳ 인스타그램 서버에서 영상 처리 중... 3분간 대기합니다.")
            time.sleep(180) 
            
            # 3. 최종 게시물 발행
            publish_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media_publish"
            publish_payload = {
                'creation_id': creation_id,
                'access_token': ACCESS_TOKEN
            }
            r_pub = requests.post(publish_url, data=publish_payload)
            if 'id' in r_pub.json():
                print("🎉 🎉 인스타그램 릴스 최종 업로드 성공! 🎉 🎉")
            else:
                print(f"❌ 최종 발행 실패: {r_pub.text}")
        else:
            # 💡 여기서 에러가 나면 권한 문제일 가능성이 높음
            print(f"❌ 컨테이너 생성 실패: {res}")
            if 'deprecated' in str(res):
                print("💡 팁: 페이스북 앱 설정에서 'Instagram Graph API'가 최신 버전인지 확인하세요.")
                
    except Exception as e:
        print(f"❌ API 요청 에러: {e}")

def get_best_sales_script(selected_topic):
    """OpenRouter 에러 방지를 위한 딜레이 보강"""
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
    prompt_content = f"Topic: {selected_topic}\nCreate a 20-word dark psychology script for Instagram. No intro."
    
    for model in AI_MODELS:
        try:
            print(f"🤖 {model} 모델에게 대본 요청 중...")
            time.sleep(5) # 429 에러 방지를 위해 대기 시간 늘림
            response = client.chat.completions.create(
                model=model, 
                messages=[{"role": "user", "content": prompt_content}],
                extra_headers={"HTTP-Referer": "https://github.com", "X-Title": "Auto Reels"} # 필수 헤더 추가
            )
            script = response.choices[0].message.content.strip().replace('"', '')
            if script:
                return script, False
        except Exception as e:
            print(f"⚠️ {model} 실패: {e}")
            continue
    
    print("🆘 모든 AI 응답 없음. 비상 대본을 사용합니다.")
    e_scripts = get_list_from_file(EMERGENCY_FILE, ["Success is the only option."])
    return random.choice(e_scripts), True

# (get_list_from_file, update_emergency_scripts, update_topics_list 등 기존 로직 유지)
# ... [나머지 함수들은 이전과 동일] ...

def run_reels_bot():
    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth"])
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
        
        # 🔗 GitHub Pages URL (이미 로그에서 성공한 주소 형식 적용)
        public_url = f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{final_video_name}"
        
        # 🚀 업로드 실행
        post_to_instagram(public_url, final_caption)
        
        # 데이터 업데이트
        if is_emergency: update_emergency_scripts(script)
        else: update_topics_list(selected_topic)

    except Exception as e:
        print(f"❌ 작업 에러: {e}")

if __name__ == "__main__":
    # 필수 함수들 누락 방지 (복사 시 주의)
    def get_list_from_file(p, d):
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f: f.write("\n".join(d))
            return d
        with open(p, "r", encoding="utf-8") as f: return [l.strip() for l in f.readlines() if l.strip()]
    
    # 여기에 나머지 update_... 함수들 생략 없이 포함하여 실행
    run_reels_bot()
