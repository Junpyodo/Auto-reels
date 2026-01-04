import os
import random
import google.generativeai as genai
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    # 현재 실행 중인 폴더 경로 확인
    current_path = os.getcwd()
    print(f"현재 작업 경로: {current_path}")

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    topics = ["Dark psychology to make her obsessed", "High-value man's silence", "Laws of power"]
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

    video = VideoFileClip("background.mp4").subclip(0, 10).colorx(0.3)
    
    txt = TextClip(script, 
                   fontsize=40, 
                   color='white', 
                   font='DejaVu-Sans-Bold', 
                   method='caption', 
                   size=(video.w*0.8, None)).set_duration(video.duration).set_pos('center').fadein(2)
    
    final = CompositeVideoClip([video, txt])
    
    # 저장 위치를 절대 경로로 명시하여 서버가 놓치지 않게 합니다.
    output_filename = "final_reels.mp4"
    output_path = os.path.join(current_path, output_filename)
    
    print(f"영상 파일 저장 시작: {output_path}")
    final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print(f"--- 영상 저장 완료: {output_filename} ---")

if __name__ == "__main__":
    run_reels_bot()
