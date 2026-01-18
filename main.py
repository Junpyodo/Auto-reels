import os
import random
import time
import json
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

AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

# -------------- 유틸 함수 --------------
def get_list_from_file(file_path):
    if not os.path.exists(file_path): return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_list_to_file(file_path, items):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(items))

def load_json(path, default):
    if not os.path.exists(path): return default
    with open(path, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try: return resp.choices[0].message.content.strip()
    except: return ""

# -------------- 핵심 로직 (프롬프트 강화) --------------
def get_best_sales_script(selected_topic):
    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    
    prompt_content = (
        f"Role: You are a high-level manipulator and master of Dark Psychology, writing for the elite 1% who seek power, success, and money.\n"
        f"Topic: {selected_topic}.\n\n"
        "Task: Create viral Instagram Reel content structure:\n"
        "1. Video Script: A 'Cold Hook' triggering immediate curiosity/fear and giving people hope that they can also be rich by doing so. They must also feel that they now found out the secret that other rich people are already doing No emojis. Some punchy sentences.\n"
        "2. Instagram Caption: A psychological 'open loop' question forcing comments.\n"
        "3. Hashtags: 10 viral dark psychology hashtags.\n\n"
        "Tone: Cold, mysterious, superior. Avoid clichés.\n"
        "IMPORTANT: Return exactly in this format: [Script] | [Caption] | [Hashtags]"
    )

    for attempt in range(3):
        model = random.choice(AI_MODELS)
        try:
            print(f"🤖 AI 시도 {attempt+1}/3 (모델: {model})")
            resp = client.chat.completions.create(
                model=model, 
                messages=[{"role":"user","content":prompt_content}],
                timeout=30 
            )
            raw_data = safe_extract_text_from_openai_response(resp)
            parts = raw_data.split('|')
            
            if len(parts) >= 3:
                script = parts[0].strip().replace('"','')
                if script not in used_scripts:
                    used_scripts.append(script)
                    save_json(USED_SCRIPTS_FILE, used_scripts)
                    print(f"✨ 새 대본 확정: {script}")
                    return script, parts[1].strip(), parts[2].strip()
        except Exception as e:
            print(f"⚠️ AI 실패: {e}")
            time.sleep(2)

    print("🚨 비상 대본을 사용합니다.")
    emergency_list = get_list_from_file(EMERGENCY_FILE)
    if not emergency_list:
        return "Control their mind before they control yours.", "Are you the hunter?", "#darkpsychology"

    chosen = random.choice(emergency_list)
    e_parts = chosen.split('|')
    script = e_parts[0].strip().replace('"','')
    
    used_scripts.append(script)
    save_json(USED_SCRIPTS_FILE, used_scripts)
    emergency_list.remove(chosen)
    save_list_to_file(EMERGENCY_FILE, emergency_list)
    
    return script, e_parts[1].strip(), e_parts[2].strip()

# -------------- 영상 제작 --------------
def create_video(script):
    try:
        print("🎬 영상 편집 시작...")
        video = VideoFileClip("background.mp4").subclip(0, 8).fx(vfx.colorx, 0.25)
        txt = TextClip(script, fontsize=45, color='white', 
                       size=(int(video.w * 0.85), None),
                       font='NanumGothic-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        
        final_clip = CompositeVideoClip([video, txt])
        if os.path.exists("music.mp3"):
            audio = AudioFileClip("music.mp3").subclip(0, 8)
            final_clip = final_clip.set_audio(audio)

        final_clip.write_videofile("reels_video.mp4", fps=24, codec="libx264", audio=os.path.exists("music.mp3"))
        return "reels_video.mp4"
    except Exception as e:
        print(f"❌ 영상 제작 실패: {e}"); return None

# -------------- 인스타그램 및 기타 기능 --------------
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

def update_topics_with_new_ideas(current_topic):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt = f"Suggest 5 new dark psychology topics for viral Reels based on '{current_topic}'. One per line, no numbering."
    try:
        resp = client.chat.completions.create(model=random.choice(AI_MODELS), messages=[{"role":"user","content":prompt}])
        new_ideas = safe_extract_text_from_openai_response(resp).split('\n')
        topics = get_list_from_file(TOPIC_FILE)
        for idea in new_ideas:
            idea = idea.strip()
            if idea and idea not in topics: topics.append(idea)
        save_list_to_file(TOPIC_FILE, topics)
    except: pass

# -------------- 실행 함수 (여기가 에러 해결 포인트!) --------------
def run_reels_bot():
    print("🚀 봇 실행 시작")
    if not os.path.exists("background.mp4"): 
        print("❌ background.mp4 파일이 없습니다."); return
    
    topics = get_list_from_file(TOPIC_FILE)
    if not topics: 
        print("❌ 주제 파일이 비어있습니다."); return
    
    selected_topic = random.choice(topics)
    print(f"🎯 선택된 주제: {selected_topic}")
    
    script, caption, hashtags = get_best_sales_script(selected_topic)
    
    final_video = create_video(script)
    if final_video:
        p_url = gh_pages_publish(final_video)
        if p_url:
            print(f"⏳ 인스타그램 업로드 대기 중... URL: {p_url}")
            time.sleep(60)
            full_caption = f"{caption}\n.\n.\n{hashtags}"
            if post_to_instagram(p_url, full_caption):
                print("✅ 인스타그램 업로드 완료!")
                update_topics_with_new_ideas(selected_topic)

if __name__ == "__main__":
    run_reels_bot()