import os
import google.generativeai as genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def run_reels_bot():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("에러: GEMINI_API_KEY를 찾을 수 없습니다.")
        return

    genai.configure(api_key=api_key)
    
    print("--- 대본 생성 시작 ---")
    # 최신 모델명으로 404 에러 방지
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        response = model.generate_content("Write a dark psychology quote about silence. 2 sentences. Max 100 chars.")
        script = response.text.replace('"', '').strip()
        print(f"생성 문구: {script}")
    except Exception as e:
        print(f"AI 생성 실패: {e}")
        return

    if not os.path.exists("background.mp4"):
        print("에러: background.mp4 파일이 없습니다.")
        return

    try:
        print("영상 편집 시작...")
        video = VideoFileClip("background.mp4").subclip(0, 7).colorx(0.3)
        
        txt = TextClip(script, fontsize=40, color='white', font='DejaVu-Sans-Bold', 
                       method='caption', size=(video.w*0.8, None)).set_duration(video.duration).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264")
        print("--- 저장 완료 ---")
    except Exception as e:
        print(f"영상 편집 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
