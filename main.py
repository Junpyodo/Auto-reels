import os
import random
import google.generativeai as genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    print("--- 영상 제작 프로세스 시작 ---")
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    topics = ["Dark psychology to make her obsessed", "The power of silence", "Habits of high-value men"]
    topic = random.choice(topics)
    
    prompt = f"Write a powerful 2-sentence dark psychology quote about {topic}. Max 100 chars. End with 'Secret in bio.'"
    
    try:
        response = model.generate_content(prompt)
        script = response.text.replace('"', '').strip()
        print(f"생성된 문구: {script}")
    except Exception as e:
        print(f"AI 대본 생성 실패: {e}")
        return

    if not os.path.exists("background.mp4"):
        print("에러: background.mp4 파일을 찾을 수 없습니다.")
        return

    # 영상 로드 및 어둡게 처리
    video = VideoFileClip("background.mp4").subclip(0, 10).colorx(0.3)
    
    # 자막 설정: 폰트 크기를 약간 줄여 안정성 확보
    txt = TextClip(script, 
                   fontsize=40, 
                   color='white', 
                   font='DejaVu-Sans-Bold', 
                   method='caption', 
                   size=(video.w*0.8, None)).set_duration(video.duration).set_pos('center').fadein(2)
    
    # 합성 및 저장
    try:
        final = CompositeVideoClip([video, txt])
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True)
        print("--- 영상 저장 완료 ---")
    except Exception as e:
        print(f"영상 합성 중 에러 발생: {e}")

if __name__ == "__main__":
    run_reels_bot()
