import os
import random
import datetime
from openai import OpenAI
from google.cloud import texttospeech
from moviepy.editor import VideoFileClip, TextClip, AudioFileClip, CompositeVideoClip

# 1. 보안 설정 (GitHub Secrets에서 가져옴)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_key.json"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_reels_bot():
    # 2. AI 문구 생성 (구매 유도)
    items = ["미니멀 가죽 지갑", "프리미엄 텀블러", "다크초콜릿 단백질바"]
    item = random.choice(items)
    prompt = f"성공을 갈망하는 남자를 위해 {item}을 사고 싶게 만드는 15초 릴스 대본을 80자 내외로 써줘. 카리스마 있는 말투로."
    
    res = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    script = res.choices[0].message.content
    print(f"대본: {script}")

    # 3. 구글 TTS 음성 생성
    tts_client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=script)
    voice = texttospeech.VoiceSelectionParams(language_code="ko-KR", name="ko-KR-Neural2-C", ssml_gender=texttospeech.SsmlVoiceGender.MALE)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, pitch=-1.5)
    
    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open("voice.mp3", "wb") as out:
        out.write(response.audio_content)

    # 4. 영상 합성 (MoviePy)
    # background.mp4 파일이 저장소에 있어야 합니다
    video = VideoFileClip("background.mp4").subclip(0, 8)
    audio = AudioFileClip("voice.mp3")
    video = video.set_audio(audio)
    
    # 자막 (중앙 배치)
    txt = TextClip(script, fontsize=40, color='white', font='Liberation-Sans-Bold', 
                   method='caption', size=(video.w*0.8, None)).set_duration(video.duration).set_pos('center')
    
    final = CompositeVideoClip([video, txt])
    final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    run_reels_bot()
