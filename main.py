import os
from genai import Client # 신규 라이브러리 방식
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def run_reels_bot():
    api_key = os.getenv("GEMINI_API_KEY")
    # 신규 SDK 클라이언트 생성
    client = Client(api_key=api_key)
    
    print("--- 신규 SDK로 대본 생성 중 ---")
    try:
        # 새로운 호출 방식 적용
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents="Write a 1-sentence dark psychology quote about power."
        )
        script = response.text.strip()
        print(f"생성 문구: {script}")
    except Exception as e:
        print(f"AI 에러: {e}")
        return

    if not os.path.exists("background.mp4"):
        print("에러: background.mp4가 없습니다.")
        return

    try:
        video = VideoFileClip("background.mp4").subclip(0, 5).colorx(0.3)
        txt = TextClip(script, fontsize=40, color='white', size=(video.w*0.8, None), 
                       font='DejaVu-Sans-Bold', method='caption').set_duration(5).set_pos('center')
        
        final = CompositeVideoClip([video, txt])
        final.write_videofile("final_reels.mp4", fps=24, codec="libx264")
        print("--- 제작 성공! ---")
    except Exception as e:
        print(f"제작 에러: {e}")

if __name__ == "__main__":
    run_reels_bot()
