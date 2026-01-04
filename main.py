import os
import sys

# 🌟 라이브러리 충돌을 강제로 방지하는 코드 추가
try:
    import importlib_metadata
except ImportError:
    pass

import google.generativeai as genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def run_reels_bot():
    print("--- 1. API 키 확인 단계 ---")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("에러: API 키가 비어있습니다.")
        return

    print("--- 2. 제미나이 연결 단계 ---")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        response = model.generate_content("Write a 1-sentence dark psychology quote.")
        script = response.text.strip()
        print(f"생성된 문구: {script}")
    except Exception as e:
        print(f"AI 생성 중 에러 발생: {e}")
        return

    print("--- 3. 영상 제작 단계 ---")
    if not os.path.exists("background.mp4"):
        print("에러: background.mp4 파일이 없습니다.")
        return

    try:
        video = VideoFileClip("background.mp4").subclip(0, 5)
        txt = TextClip(script, fontsize=40, color='white', size=(video.w*0.8, None), method='caption')
        txt = txt.set_duration(video.duration).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264")
        print("--- 4. 최종 저장 완료! ---")
    except Exception as e:
        print(f"영상 편집 중 에러 발생: {e}")

if __name__ == "__main__":
    run_reels_bot()
