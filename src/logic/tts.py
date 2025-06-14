"""
For more samples please visit https://github.com/Azure-Samples/cognitive-services-speech-sdk
"""

from dotenv import load_dotenv
import os
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

speech_key = os.getenv("AZURE_SPEECH_API_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
# speech_config.speech_synthesis_voice_name = "pl-PL-ZofiaNeural"
speech_config.speech_synthesis_voice_name = "pl-PL-MarekNeural"


def text_to_speech(input: str, filename: str = "output.mp3"):
    audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    result = speech_synthesizer.speak_text_async(input).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"✅ Speech synthesized and saved to {filename}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("❌ Synthesis canceled:", cancellation_details.reason)
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details:", cancellation_details.error_details)


if __name__ == "__main__":
    output = text_to_speech(
        "Witajcie w naszym edukacyjnym podkaście poświęconym "
        "fascynującemu światu słoni. Dziś zanurzymy się w niezwykłe cechy tych majestatycznych stworzeń, "
        "ich zachowania oraz rolę, jaką odgrywają w ekosystemach na całym świecie."
    )
