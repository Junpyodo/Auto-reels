import os
import random
import google.generativeai as genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

# 1. 제미나이 설정 (TTS 미사용으로 구글 키 설정 불필요)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    print("--- 다크 심리학 텍스트 릴스 모드 시작 ---")
    
    # 2. 다크 심리학 및 성공 주제 추가
    items = ["High-purity Maca Supplement", "Deep Focus Nootropics", "The Elite Mindset PDF"]
    topics = [
        "Dark psychology to make her obsessed", # 여자가 끌리는 다크 심리학
        "The power of silence in attraction",    # 유혹에서의 침묵의 힘
        "Ancient Stoic Wisdom on Power",         # 권력에 대한 스토아 철학
        "Habits of the 1% Undefeated Men",       # 상위 1% 남자의 습관
        "The mystery of a high-value man"        # 고가치 남성의 신비로움
    ]
    
    item = random.choice(items)
    topic = random.choice(topics)
    
    # 3. 제미나이 대본 생성 (더 짧고 강렬하게)
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Create a powerful, short 2-sentence quote about '{topic}'.
    Make it sound mysterious, dark, and masculine. 
    Use a psychological trigger that makes people curious about '{item}'.
    Format:
    [Sentence 1: A cold truth about life or attraction]
    [Sentence 2: A subtle hint that the secret lies in your ritual]
    Ending: "The secret is in the bio."
    Maximum 120 characters total. No hashtags.
    """
    
    response = model.generate_content(prompt)
    script = response.text.replace('"', '') # 따옴표 제거
    print(f"생성된 스크립트: {script}")

    # 4. 영상 합성
    # background.mp4는 이미 음악이 포함된 어두운 영상이어야 합니다.
    video = VideoFileClip("background.mp4").subclip(0, 10)
    
    # 영상을 매우 어둡게 보정 (시각적 무게감)
    video = video.colorx(0.3) 
    
    # 5. 강력한 폰트 및 자막 설정
    # 'Liberation-Sans-Bold'는 대부분의 리눅스 서버에 기본 설치된 굵고 강한 폰트입니다.
    # 더 화려한 폰트를 원하시면 아래 폰트 이름을 'Impact' 또는 'Arial-Bold'로 시도해 보세요.
    txt = TextClip(script, 
                   fontsize=40, 
                   color='white', 
                   font='Liberation-Sans-Bold', 
                   method='caption', 
                   align='center',
                   size=(video.w*0.8, None),
                   line_spacing=10)
    
    # 텍스트가 2초 동안 서서히 나타남 (Fade In)
    txt = txt.set_duration(video.duration).set_pos('center').fadein(2)
    
    final = CompositeVideoClip([video, txt])
    
    # 최종 결과물 저장
    final.write_videofile("final_reels.mp4", fps=24, codec="libx264")
    print("--- 제작 완료: final_reels.mp4 ---")

if __name__ == "__main__":
    run_reels_bot()
