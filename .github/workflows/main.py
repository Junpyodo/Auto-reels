import os
import random
import google.generativeai as genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# 제미나이 설정
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    print("--- 텍스트 전용 다크 심리학 모드 시작 ---")
    
    items = ["High-purity Maca Supplement", "Deep Focus Nootropics", "The Elite Mindset PDF"]
    topics = [
        "Dark psychology to make her obsessed",
        "The power of silence in attraction",
        "Ancient Stoic Wisdom on Power",
        "Habits of the 1% Undefeated Men",
        "The cold truth about human nature"
    ]
    
    item = random.choice(items)
    topic = random.choice(topics)
    
    # 모델명을 최신 버전인 'gemini-1.5-flash'로 변경하여 404 에러 해결
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
        script = response.text.replace('"', '')
        print(f"Generated Script: {script}")
    except Exception as e:
        print(f"Script Generation Failed: {e}")
        return

    # 영상 합성 단계
    if not os.path.exists("background.mp4"):
        print("Error: background.mp4 파일을 찾을 수 없습니다.")
        return

    video = VideoFileClip("background.mp4").subclip(0, 10)
    video = video.colorx(0.3) 
    
    txt = TextClip(script, 
                   fontsize=45, 
                   color='white', 
                   font='DejaVu-Sans-Bold', 
                   method='caption', 
                   align='center',
                   size=(video.w*0.85, None),
                   line_spacing=12)
    
    txt = txt.set_duration(video.duration).set_pos('center').fadein(2.5)
    
    final = CompositeVideoClip([video, txt])
    
    # 최종 파일 저장 (이 이름이 run.yml과 일치해야 함)
    final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio_codec="aac")
    print("--- 제작 완료: final_reels.mp4 ---")

if __name__ == "__main__":
    run_reels_bot()
