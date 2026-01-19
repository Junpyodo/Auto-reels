import os
import random
import time
import json
import traceback
import requests
import subprocess
import re
from openai import OpenAI
# [수정] AudioFileClip 추가
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx.all as vfx

# optional AWS helper (있으면 사용)
try:
    from aws_upload import upload_file_to_s3
except Exception:
    upload_file_to_s3 = None

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
MENTIONS = "@instagram"

AI_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free",
    "openai/gpt-4o-mini-2024-07-18:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]

# -------------- 유틸 (기존과 동일) --------------
def get_list_from_file(file_path, default_values):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(default_values))
        return default_values[:]
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def save_list_to_file(file_path, items):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(items))

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_extract_text_from_openai_response(resp):
    try:
        if isinstance(resp, dict):
            if "choices" in resp and len(resp["choices"]) > 0:
                ch0 = resp["choices"][0]
                if "message" in ch0 and isinstance(ch0["message"], dict) and "content" in ch0["message"]:
                    return ch0["message"]["content"].strip()
                if "text" in ch0 and ch0["text"]:
                    return ch0["text"].strip()
        if hasattr(resp, "choices") and len(resp.choices) > 0:
            ch0 = resp.choices[0]
            if hasattr(ch0, "message") and hasattr(ch0.message, "content"):
                return ch0.message.content.strip()
            if hasattr(ch0, "text"):
                return ch0.text.strip()
    except Exception:
        pass
    return ""

# -------------- AI 관련 (기존과 동일) --------------
def update_emergency_scripts(current_topic=None, used_script=None):
    scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence.", "Success is the best revenge."])
    
    if used_script:
        scripts = [s for s in scripts if s.strip().rstrip('.') != used_script.strip().rstrip('.')]

    if not OPENROUTER_API_KEY:
        save_list_to_file(EMERGENCY_FILE, scripts)
        return

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    
    topic_str = f"based on the topic '{current_topic}'" if current_topic else "about dark psychology and wealth"
    prompt = f"Generate 10 powerful, viral 20-word scripts for Instagram Reels {topic_str}. One per line. No numbers, no quotes."

    for model in AI_MODELS:
        try:
            time.sleep(1)
            resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
            text = safe_extract_text_from_openai_response(resp)
            if not text: continue
            new_list = [line.strip().replace('"','') for line in text.split("\n") if len(line.strip()) > 5]
            if new_list:
                combined = list(dict.fromkeys(scripts + new_list))
                save_list_to_file(EMERGENCY_FILE, combined)
                print(f"✅ 비상 대본 업데이트 완료 ({model})")
                return
        except: continue
    save_list_to_file(EMERGENCY_FILE, scripts)
    print("⚠️ 모든 모델 실패 — emergency 리스트는 유지됨")

# ... (AI 모델 반복문 종료 후) ...

    # 모든 AI 모델이 실패하거나 중복만 생성할 경우 비상 대본 섹션
    print("🆘 모든 AI 모델이 중복을 생성함. 비상 대본 중에서 미사용본 탐색 중...")
    e_scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence."])
    
    # [강화된 로직] 사용하지 않은 비상 대본만 필터링
    fresh_emergency = [s for s in e_scripts if normalize(s) not in normalized_used_scripts]
    
    if fresh_emergency:
        chosen = random.choice(fresh_emergency)
        print(f"⚠️ 비상 대본 사용: {chosen}")
    else:
        # 비상 대본까지 다 썼을 경우: 여기서 그냥 중복을 내보내면 영상이 똑같아짐
        # 해결책: 강제로 아주 생소한 문장을 하나 생성하거나 에러를 발생시켜 중단
        fallback_list = [
            "Privacy is power. What they don't know, they can't ruin.",
            "Don't go broke trying to look rich. Build in silence.",
            "The best revenge is massive success and zero words."
        ]
        # fallback 중에서도 안 쓴 것 찾기
        very_fresh = [s for s in fallback_list if normalize(s) not in normalized_used_scripts]
        chosen = random.choice(very_fresh) if very_fresh else "Time is the only asset you can't buy back."
        print(f"🚨 최후의 보루 스크립트 사용: {chosen}")
    
    # 최종 선택된 대본 저장 (중요: 이래야 다음번에 또 안 씀)
    used_scripts.append(chosen)
    save_json(USED_SCRIPTS_FILE, used_scripts)
    return chosen, True

def update_topics_list(used_topic):
    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY가 없습니다 — 주제 업데이트 건너뜀")
        return

    topics = get_list_from_file(TOPIC_FILE, ["Wealth psychology"])
    if used_topic in topics:
        topics.remove(used_topic)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    prompt = f"Based on {used_topic}, generate 10 new Instagram Reel topics about dark psychology and wealth. Newlines only."

    for model in AI_MODELS:
        try:
            time.sleep(1)
            resp = client.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
            text = safe_extract_text_from_openai_response(resp)
            if not text:
                continue
            new_topics = [line.strip() for line in text.split("\n") if line.strip()]
            if new_topics:
                combined = list(dict.fromkeys(topics + new_topics))
                save_list_to_file(TOPIC_FILE, combined)
                print(f"✅ 주제 리스트 업데이트 완료 ({model})")
                return
        except Exception as e:
            print(f"⚠️ update_topics_list: {model} 실패: {e}")
            continue
    print("⚠️ 모든 모델 실패 — 주제 리스트 변경 안됨")

def get_best_sales_script(selected_topic, max_attempts_per_model=2):
    if not OPENROUTER_API_KEY:
        e_scripts = get_list_from_file(EMERGENCY_FILE, ["The 1% don't sleep until the job is done."])
        return random.choice(e_scripts), True

    used_scripts = load_json(USED_SCRIPTS_FILE, [])
    
    def normalize(text):
        return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

    normalized_used_scripts = [normalize(s) for s in used_scripts]
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    
    prompt_content = f"""
    Topic: {selected_topic}
    Role: You are a viral content creator specializing in Dark Psychology and Wealth Mindset that knows secret which only rich people knows.
    Objective: Create a script for a viral Instagram Reel. (can be a bullet point style. like, top 5 things only rich knows...). After seeing this they must feel like they must buy the thing in my bio.
    
    Guidelines:
    - Use the "Pattern Interrupt" technique: Start with a shocking truth or a counter-intuitive statement.
    - Focus on high-status, dark psychology, or "the hidden secrets of the 1%".
    - Tone: Cold, authoritative, and mysterious. Avoid clichés like "believe in yourself" or "work hard".
    - Structure: A powerful statement that makes the viewer feel they are missing out or being lied to.
    
    Provide ONLY the script. No quotes, no intro.
    """

    print(f"🤖 중복 체크 모드 가동 (현재 저장된 대본: {len(used_scripts)}개)")
    
    for model in AI_MODELS:
        for attempt in range(max_attempts_per_model):
            try:
                time.sleep(1.2)
                resp = client.chat.completions.create(
                    model=model, 
                    messages=[{"role":"user","content":prompt_content}],
                    temperature=0.95
                )
                raw_script = safe_extract_text_from_openai_response(resp)
                
                if not raw_script: continue
                
                script = raw_script.split('\n')[0].strip().replace('"', '')
                current_norm = normalize(script)
                
                if current_norm in normalized_used_scripts:
                    print(f"🚫 중복 감지 및 차단 ({model}): {script[:30]}...")
                    continue 
                
                if len(current_norm) < 15:
                    continue

                print(f"✨ [신규 대본 확정] 모델: {model}\n내용: {script}")
                used_scripts.append(script)
                save_json(USED_SCRIPTS_FILE, used_scripts)
                return script, False
                
            except Exception as e:
                print(f"⚠️ {model} 에러: {e}")
                continue

    # 모든 AI 모델이 실패하거나 중복만 생성할 경우
    print("🆘 모든 모델 중복 또는 실패 — 비상 대본 사용")
    e_scripts = get_list_from_file(EMERGENCY_FILE, ["Work in silence."])
    fresh_emergency = [s for s in e_scripts if normalize(s) not in normalized_used_scripts]
    
    if fresh_emergency:
        chosen = random.choice(fresh_emergency)
    
    # 비상 대본도 다 썼을 때를 위한 최후의 한 문장
    else:
        chosen = "Privacy is power. What they don't know, they can't ruin."
    
    print(f"⚠️ 선택된 대본: {chosen}")
    
    used_scripts.append(chosen)
    save_json(USED_SCRIPTS_FILE, used_scripts)
    return chosen, True

# -------------- 업로드 관련 (기존과 동일) --------------
def upload_to_0x0(file_path, max_attempts=2):
    url = "https://0x0.st"
    for attempt in range(max_attempts):
        try:
            with open(file_path,"rb") as f:
                files={'file':(os.path.basename(file_path), f)}
                r = requests.post(url, files=files, timeout=60)
            if r.status_code in (200,201) and r.text.strip().startswith("http"):
                return r.text.strip()
            else:
                print(f"⚠️ 0x0.st 실패({r.status_code}):{r.text}")
        except Exception as e:
            print("⚠️ 0x0.st 예외:", e)
        time.sleep(2*(attempt+1))
    return None

def upload_to_transfersh(file_path, max_attempts=2):
    for attempt in range(max_attempts):
        try:
            url = f"https://transfer.sh/{os.path.basename(file_path)}"
            with open(file_path,"rb") as f:
                r = requests.put(url, data=f, timeout=120)
            if r.status_code in (200,201):
                return r.text.strip()
            else:
                print(f"⚠️ transfer.sh 실패({r.status_code}): {r.text}")
        except Exception as e:
            print("⚠️ transfer.sh 예외:", e)
        time.sleep(2*(attempt+1))
    return None

def gh_pages_publish(file_path):
    if not GITHUB_TOKEN:
        print("ℹ️ GITHUB_TOKEN이 없어 gh-pages 배포 불가.")
        return None
    try:
        dest_path = os.path.basename(file_path)
        repo_url = f"https://x-access-token:{GITHUB_TOKEN}@github.com/{GITHUB_ID}/{REPO_NAME}.git"
        workdir = "/tmp/auto-reels-ghpages"
        
        subprocess.run(["rm", "-rf", workdir], check=False)
        subprocess.run(["git", "clone", repo_url, workdir], check=True)
        
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=workdir, check=True)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=workdir, check=True)

        ret = subprocess.run(["git", "checkout", "gh-pages"], cwd=workdir, capture_output=True)
        if ret.returncode != 0:
            print("🌱 gh-pages 브랜치를 새로 생성합니다.")
            subprocess.run(["git", "checkout", "--orphan", "gh-pages"], cwd=workdir, check=True)
            subprocess.run(["git", "rm", "-rf", "."], cwd=workdir, check=True)

        dest = os.path.join(workdir, dest_path)
        subprocess.run(["cp", file_path, dest], check=True)
        subprocess.run(["git", "add", dest_path], cwd=workdir, check=True)
        subprocess.run(["git", "commit", "-m", "🚀 Add latest reel video"], cwd=workdir, check=True)
        subprocess.run(["git", "push", "origin", "gh-pages"], cwd=workdir, check=True)
        
        public_url = f"https://{GITHUB_ID}.github.io/{REPO_NAME}/{dest_path}"
        print("🔗 gh-pages 업로드 완료:", public_url)
        return public_url
    except Exception as e:
        print("❌ gh-pages 업로드 실패:", e)
        return None

def upload_video_and_get_public_url(file_path):
    if upload_file_to_s3:
        try:
            print("🔼 S3 업로드 시도...")
            s3_url = upload_file_to_s3(file_path)
            if s3_url:
                print("🔗 S3 업로드 성공:", s3_url)
                return s3_url
        except Exception as e:
            print("⚠️ S3 업로드 예외:", e)

    gh_url = gh_pages_publish(file_path)
    if gh_url:
        return gh_url

    print("🔼 0x0.st 업로드 시도...")
    url = upload_to_0x0(file_path)
    if url: return url

    print("🔼 transfer.sh 업로드 시도...")
    url = upload_to_transfersh(file_path)
    if url: return url

    print("❌ 공개 URL 생성 실패")
    return None

# -------------- Instagram 업로드 (기존과 동일) --------------
def post_to_instagram(video_url, caption, api_version="v19.0"):
    ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

    if not ACCESS_TOKEN or not ACCOUNT_ID:
        print("❌ INSTAGRAM_ACCESS_TOKEN 또는 INSTAGRAM_ACCOUNT_ID가 설정되어 있지 않습니다.")
        return False

    print("📤 인스타 업로드 시도. URL:", video_url)
    container_url = f"https://graph.facebook.com/{api_version}/{ACCOUNT_ID}/media"
    payload = {
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption,
        'share_to_feed': 'true', 
        'access_token': ACCESS_TOKEN
    }
    
    try:
        r = requests.post(container_url, data=payload, timeout=30)
        res = r.json()
        if "id" not in res:
            print("❌ 컨테이너 생성 실패:", res)
            return False
            
        creation_id = res.get("id")
        print("⏳ 인스타그램 서버에서 영상 처리 상태 확인 중...")
        status_url = f"https://graph.facebook.com/{api_version}/{creation_id}"
        status_params = {'fields': 'status_code', 'access_token': ACCESS_TOKEN}
        
        for i in range(20):
            time.sleep(5)
            check_r = requests.get(status_url, params=status_params, timeout=30)
            status_res = check_r.json()
            status_code = status_res.get("status_code", "").upper()
            print(f"   - 상태 확인 ({i+1}/20): {status_code}")
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                print("❌ 영상 처리 중 에러 발생:", status_res)
                return False

        publish_url = f"https://graph.facebook.com/{api_version}/{ACCOUNT_ID}/media_publish"
        publish_payload = {'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
        r_pub = requests.post(publish_url, data=publish_payload, timeout=30)
        pub_res = r_pub.json()
        
        if 'id' in pub_res:
            print("🎉 업로드 성공! 게시물 ID:", pub_res.get("id"))
            return True
        else:
            print("❌ 최종 게시 실패:", pub_res)
            return False
    except Exception as e:
        print("❌ API 예외 발생:", e)
        return False

# -------------- 메인 흐름 (음악 추가 부분 적용) --------------
def run_reels_bot():
    if not os.path.exists("background.mp4"):
        print("❌ background.mp4 파일이 필요합니다.")
        return

    topics = get_list_from_file(TOPIC_FILE, ["Dark psychology of wealth"])
    selected_topic = random.choice(topics)
    print("🎯 주제:", selected_topic)

    script, is_emergency = get_best_sales_script(selected_topic)
    final_caption = f"{script}\n\n{MENTIONS}\n\n{HASHTAGS}"

    try:
        print("🎬 영상 편집 시작...")
        video = VideoFileClip("background.mp4").subclip(0,8).fx(vfx.colorx, 0.25)
        
        txt = TextClip(script, fontsize=45, color='white', size=(int(video.w*0.85), None),
                       font='DejaVu-Sans-Bold', method='caption', align='center',
                       interline=12, stroke_color='black', stroke_width=1.5).set_duration(8).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        
        audio_success = False
        if os.path.exists("music.mp3"):
            try:
                print("🎵 음악 합성 중 (music.mp3)...")
                music = AudioFileClip("music.mp3").subclip(0, 8) 
                final = final.set_audio(music)
                audio_success = True
            except Exception as ae:
                print(f"⚠️ 음악 추가 중 오류 발생 (무음으로 계속): {ae}")
        else:
            print("ℹ️ music.mp3 파일이 없어 음악 없이 제작합니다.")

        final_video_name = "reels_video.mp4"
        final.write_videofile(final_video_name, fps=24, codec="libx264", audio=audio_success)
        
    except Exception as e:
        print("❌ 영상 제작 오류:", e)
        return

    public_url = upload_video_and_get_public_url(final_video_name)
    if not public_url:
        print("❌ 공개 URL 생성 실패.")
        return

    print("⏳ 배포 안정화를 위해 60초 대기 후 인스타그램 전송을 시작합니다...")
    time.sleep(60)

    success = post_to_instagram(public_url, final_caption)
    
    if success:
        print("✅ 모든 프로세스가 성공적으로 완료되었습니다!")
        if is_emergency:
            update_emergency_scripts(current_topic=selected_topic, used_script=script)
        else:
            update_topics_list(used_topic=selected_topic)
            update_emergency_scripts(current_topic=selected_topic)
    else:
        print("⚠️ 업로드 실패. 로그를 확인해 주세요.")

if __name__ == "__main__":
    run_reels_bot()
