from pydub import AudioSegment

wav_audio = AudioSegment.from_wav("f/louder_output.wav")

mp3_audio = wav_audio.export("f/louder.mp3", format="mp3")