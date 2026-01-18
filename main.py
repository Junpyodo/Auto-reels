import os
import random
import time
import json
import traceback
import requests
import subprocess
from openai import OpenAI
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx.all as vfx

# --- 설정 ---
GITHUB_ID = "Junpyodo"
REPO_NAME = "Auto-reels"
TOPIC_FILE = "topics.txt"
EMERGENCY_FILE = "emergency_scripts.txt"
USED_SCRIPTS_FILE = "used_scripts.json"

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HASHTAGS = "#wealth #success #darkpsychology #motivation #millionaire #mindset"

AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

# -------------- 유틸 --------------
def get_list_from_file(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_list_to_file(file_path, items):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(items))

def load_json(path, default):
    if not os.path.exists(path):
        save_json(path, default)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try:
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            return resp.choices[0].message.content.strip()
    except: pass
    return ""

# -------------- AI 핵심 로직 (중복 무한 체크 + 새로운 주제 추가) --------------
def get_best_sales_script(selected_topic):
    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    
    # AI 명령 수정: 형식(Script|Caption|Hashtags)을 명확하게 지시
    prompt_content = (
        f"Role: High-status Dark Psychology master for the elite 1%.\n"
        f"Topic: {selected_topic}.\n\n"
        "Task: Create viral Instagram Reel content.\n"
        "1. Video Script: A cold, predatory one-sentence hook (No emojis).\n"
        "2. Instagram Caption: One intriguing question for the audience.\n"
        "3. Hashtags: 10 viral dark psychology hashtags.\n"
        "IMPORTANT: You must return the result exactly in this format: [Script] | [Caption] | [Hashtags]"
    )

    # 최대 3번까지 AI 시도
    for attempt in range(3):
        model = random.choice(AI_MODELS)
        try:
            print(f"🤖 AI 시도 중... (시도 {attempt+1}/3, 모델: {model})")
            resp = client.chat.completions.create(
                model=model, 
                messages=[{"role":"user","content":prompt_content}],
                timeout=30 
            )
            raw_data = safe_extract_text_from_openai_response(resp)
            
            # AI 응답을 '|' 기준으로 분리
            parts = raw_data.split('|')
            
            if len(parts) >= 3:
                script = parts[0].strip().replace('"','')
                caption = parts[1].strip()
                hashtags = parts[2].strip()
                
                if script not in used_scripts:
                    used_scripts.append(script)
                    save_json(USED_SCRIPTS_FILE, used_scripts)
                    print(f"✨ 새 대본 확정: {script}")
                    return script, caption, hashtags
            
            print(f"🔄 AI가 형식을 지키지 않음. 다시 시도합니다.")
        except Exception as e:
            print(f"⚠️ AI 시도 실패: {e}")
            time.sleep(2)

    # --- AI가 3번 모두 실패했을 때 실행되는 비상 로직 ---
    print("🚨 AI 응답 실패. 비상 대본(Emergency Scripts)을 사용합니다.")
    emergency_list = get_list_from_file(EMERGENCY_FILE)
    
    if not emergency_list:
        # 비상 파일이 없을 때를 대비한 최후의 보루
        return "Control their mind before they control yours.", "Are you the hunter or the prey?", "#darkpsychology #power"

    chosen = random.choice(emergency_list)
    try:
        e_parts = chosen.split('|')
        return e_parts[0].strip(), e_parts[1].strip(), e_parts[2].strip()
    except:
        return chosen.strip(), "Master your mind.", "#darkpsychology #success"
   
def update_topics_with_new_ideas(current_topic):
    """현재 주제를 바탕으로 새로운 주제 5개를 추가함 (기존 주제 삭제 안함)"""
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt = f"Based on the topic '{current_topic}', suggest 5 new dark psychology topics for viral Instagram Reels. Write only the topics, one per line, no numbering."
    
    try:
        resp = client.chat.completions.create(model=random.choice(AI_MODELS), messages=[{"role":"user","content":prompt}])
        new_ideas = safe_extract_text_from_openai_response(resp).split('\n')
        
        topics = get_list_from_file(TOPIC_FILE)
        # 중복되지 않는 새로운 아이디어만 추가
        for idea in new_ideas:
            idea = idea.strip()
            if idea and idea not in topics:
                topics.append(idea)
        
        save_list_to_file(TOPIC_FILE, topics)
        print(f"✅ 새로운 주제 5개가 추가되었습니다.")
    except:
        print("⚠️ 새로운 주제 추가 실패 (다음 실행 시 재시도)")

# -------------- 영상 제작 (음악 1개 고정 + 자막 스타일) --------------
def create_video(script):
    try:
        print("🎬 영상 편집 및 음악 합성 시작...")
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        
        txt = TextClip(script, fontsize=45, color='white', 
                       size=(int(video.w * 0.85), None),
                       font='DejaVu-Sans-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        
        final_clip = CompositeVideoClip([video, txt])
        
        if os.path.exists("music.mp3"):
            audio = AudioFileClip("music.mp3").subclip(0, 8)
            final_clip = final_clip.set_audio(audio)
            print("🎵 music.mp3 배경음악 적용 완료")

        final_video_name = "reels_video.mp4"
        final_clip.write_videofile(final_video_name, fps=24, codec="libx264", audio=os.path.exists("music.mp3"))
        return final_video_name
    except Exception as e:
        print(f"❌ 영상 제작 에러: {e}")
        return None

# -------------- 업로드 및 실행 --------------
def gh_pages_publish(file_path):
    if not GITHUB_TOKEN: return None
    try:
        dest_path = os.path.basename(file_path)
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        workdir = "/tmp/auto-reels-ghpages"
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", repo_url, workdir], check=True)
        subprocess.run(["cp", file_path, os.path.join(workdir, dest_path)], check=True)
        subprocess.run(["git", "add", "."], cwd=workdir, check=True)
        subprocess.run(["git", "commit", "-m", "🚀 Add Reel"], cwd=workdir, check=True)
        subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir, check=True)
        return f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{dest_path}"
    except: return None

def post_to_instagram(video_url, caption):
    api_url = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media"
    payload = {'media_type': 'REELS', 'video_url': video_url, 'caption': caption, 'access_token': ACCESS_TOKEN}
    try:
        r = requests.post(api_url, data=payload).json()
        creation_id = r["id"]
        for _ in range(20):
            time.sleep(10)
            status = requests.get(f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={ACCESS_TOKEN}").json()
            if status.get("status_code") == "FINISHED": break
        requests.post(f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN})
        return True
    except: return False

def run_reels_bot():
    if not os.path.exists("background.mp4"): return
    
    # 1. 주제 선택
    topics = get_list_from_file(TOPIC_FILE)
    if not topics:
        print("❌ topics.txt 파일이 비어있습니다.")
        return
        
    selected_topic = random.choice(topics)
    print(f"🎯 선택된 주제: {selected_topic}")
    
    # 2. 대본, 캡션, 해시태그 생성 (수정된 부분: 3개 변수로 받음)
    script, caption, hashtags = get_best_sales_script(selected_topic)
    
    # 3. 영상 제작 (영상 안에는 'script'만 자막으로 들어감)
    final_video = create_video(script)

    if final_video:
        p_url = gh_pages_publish(final_video)
        if p_url:
            print("⏳ 인스타그램 서버 업로드 대기 중 (60초)...")
            time.sleep(60)
            
            # 4. 인스타그램 게시 (AI가 만든 캡션과 해시태그 사용)
            # 형식: [AI 질문 캡션]
            #       .
            #       [AI 해시태그]
            full_caption = f"{caption}\n.\n.\n{hashtags}"
            
            if post_to_instagram(p_url, full_caption):
                print(f"✅ 업로드 완료! (사용한 캡션: {caption})")
                # 5. 새로운 주제 보충
                update_topics_with_new_ideas(selected_topic)