from kokoro import KPipeline
import soundfile as sf
import torch
import sounddevice as sd


pipeline = KPipeline(lang_code="a")
text = """
TT3DE is a fun 3 D engine in Python for making games and visualizations in ASCII Art"""
generator = pipeline(text, voice="af_sky")
for i, (gs, ps, audio) in enumerate(generator):
    print(i, gs, ps)
    sf.write(f"{i}.wav", audio, 24000)

sd.play(audio, 24000, blocking=True)
[
    "af_alloy.pt",
    "af_aoede.pt",
    "af_bella.pt",
    "af_heart.pt",
    "af_jessica.pt",
    "af_kore.pt",
    "af_nicole.pt",
    "af_nova.pt",
    "af_river.pt",
    "af_sarah.pt",
    "af_sky.pt",
    "am_adam.pt",
    "am_echo.pt",
    "am_eric.pt",
    "am_fenrir.pt",
    "am_liam.pt",
    "am_michael.pt",
    "am_onyx.pt",
    "am_puck.pt",
    "am_santa.pt",
]
