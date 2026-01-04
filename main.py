import os
import random
import google.generativeai as genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# 1. 제미나이 설정 (TTS 미사용으로 구글 키 설정 불필요)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    print("--- 텍스트 전용 다크 심리학 모드 시작 ---")
    
    # 2. 다크 심리학 및 성공 주제 리스트
    items = ["High-purity Maca Supplement", "Deep Focus Nootropics", "The Elite Mindset PDF"]
    topics = [
        "Dark psychology to make her obsessed", # 여자가 끌리는 다크 심리학
        "The power of silence in attraction",    # 유혹에서의 침묵의 힘
        "Ancient Stoic Wisdom on Power",         # 권력에 대한 스토아 철학
        "Habits of the 1% Undefeated Men",       # 상위 1% 남자의 습관
        "The cold truth about human nature"      # 인간 본성에 대한 차가운 진실
    ]
    
    item = random.choice(items)
    topic = random.choice(topics)
    
    # 3. 제미나이 대본 생성 (더 짧고 강렬하게)
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Create a powerful, short 2-sentence quote about '{topic}'.
    Tone: Authoritative, dark, and elite. 
    Use a psychological trigger that makes people curious about '{item}'.
    - Sentence 1: A sharp, cold realization.
    - Sentence 2: A hint that the true secret is hidden.
    Ending: "The secret is in the bio."
    Total length: Max 120 characters. No hashtags or emojis.
    """
    
    try:
        response = model.generate_content(prompt)
        script = response.text.replace('"', '') # 불필요한 따옴표 제거
        print(f"Generated Script: {script}")
    except Exception as e:
        print(f"Script Generation Failed: {e}")
        return

    # 4. 영상 합성
    # 업로드하신 background.mp4가 음악이 포함된 10초 내외 영상이어야 합니다.
    video = VideoFileClip("background.mp4").subclip(0, 10)
    
    # 영상을 매우 어둡게(밝기 30%) 보정하여 자막 집중도를 높임
    video = video.colorx(0.3) 
    
    # 5. 자막 설정 (강력하고 고급스러운 폰트 스타일)
    # 'DejaVu-Sans-Bold'는 리눅스 서버에서 가장 안정적이고 굵은 폰트 중 하나입니다.
    txt = TextClip(script, 
                   fontsize=45, 
                   color='white', 
                   font='DejaVu-Sans-Bold', 
                   method='caption', 
                   align='center',
                   size=(video.w*0.85, None),
                   line_spacing=12)
    
    # 전체 텍스트가 2.5초에 걸쳐 아주 천천히 나타나도록 설정 (Fade In)
    txt = txt.set_duration(video.duration).set_pos('center').fadein(2.5)
    
    final = CompositeVideoClip([video, txt])
    
    # 6. 최종 파일 저장
    final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio_codec="aac")
    print("--- 제작 완료: final_reels.mp4 ---")

if __name__ == "__main__":
    run_reels_bot()
