import os
import random
import google.generativeai as genai
from google.cloud import texttospeech
from moviepy.editor import VideoFileClip, TextClip, AudioFileClip, CompositeVideoClip

# 보안 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_key.json"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_reels_bot():
    # 1. 판매 아이템 및 주제 설정
    items = ["고함량 마카 영양제", "무자본 창업 공략집", "성공한 남자의 향수", "집중력 향상 뇌 영양제"]
    topics = ["고대 철학자의 명언", "현대 성공의 법칙", "남성성의 본질", "패배자의 습관"]
    
    item = random.choice(items)
    topic = random.choice(topics)
    
    # 2. 제미나이 미스터리 프롬프트
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    당신은 신비롭고 압도적인 분위기의 철학적 마케터입니다.
    오늘의 주제는 '{topic}'이며, 홍보할 물건은 '{item}'입니다.
    
    [작성 규칙]
    1. 처음에는 인생의 본질을 꿰뚫는 무거운 문장으로 시작하세요.
    2. 중간에 은연중에 '{item}'의 효능이나 가치를 언급하되, 직접적으로 이름을 말하지 마세요. 
       대신 "그 비밀은 내 손끝에 있다" 혹은 "남모르게 삼키는 결단" 등으로 비유하세요.
    3. 시청자가 "저게 대체 뭐길래?"라는 갈증을 느끼게 하세요.
    4. 80자 이내로, 매우 낮고 느린 어조에 어울리는 문체로 작성하세요.
    5. 마지막 문구는 "비밀은 프로필에 남겨두었다."로 고정하세요.
    """
    
    response = model.generate_content(prompt)
    script = response.text
    print(f"생성된 미스터리 대본: {script}")

    # 3. 구글 TTS (가장 깊고 무거운 목소리 설정)
    tts_client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=script)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR", 
        name="ko-KR-Neural2-C", 
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    # 속도를 늦추고(0.9) 톤을 낮춰서(-3.0) 무겁게 만듭니다
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=-3.0, 
        speaking_rate=0.9
    )
    
    res = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open("voice.mp3", "wb") as out:
        out.write(res.audio_content)

    # 4. 영상 합성 (어두운 배경 처리)
    video = VideoFileClip("background.mp4").subclip(0, 10)
    # 영상을 어둡게 만들기 (밝기 0.5배)
    video = video.fx(lambda v: v.multiply_speed(1)).margin(top=0, opacity=0).colorx(0.5)
    
    audio = AudioFileClip("voice.mp3")
    video = video.set_audio(audio)
    
    # 자막: 폰트를 고급스럽게, 위치를 약간 아래로 조정
    txt = TextClip(script, fontsize=35, color='gray80', font='Liberation-Sans-Bold', 
                   method='caption', size=(video.w*0.7, None)).set_duration(video.duration).set_pos(('center', 'center'))
    
    final = CompositeVideoClip([video, txt])
    final.write_videofile("final_reels.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    run_reels_bot()
