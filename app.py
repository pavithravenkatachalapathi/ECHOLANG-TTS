from flask import Flask, render_template, request
from transformers import MarianMTModel, MarianTokenizer
from gtts import gTTS
from pathlib import Path
from functools import lru_cache
import uuid


# ==========================================
# Flask Application
# ==========================================

app = Flask(__name__)


# ==========================================
# Configuration
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

AUDIO_DIR = BASE_DIR / "static" / "audio"

# Create audio folder if it does not exist
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# Supported Languages
# ==========================================

LANGUAGES = {
    "hi": {
        "name": "Hindi",
        "flag": "🇮🇳",
        "model": "Helsinki-NLP/opus-mt-en-hi",
        "tts": "hi"
    },

    "es": {
        "name": "Spanish",
        "flag": "🇪🇸",
        "model": "Helsinki-NLP/opus-mt-en-es",
        "tts": "es"
    },

    "fr": {
        "name": "French",
        "flag": "🇫🇷",
        "model": "Helsinki-NLP/opus-mt-en-fr",
        "tts": "fr"
    },

    "de": {
        "name": "German",
        "flag": "🇩🇪",
        "model": "Helsinki-NLP/opus-mt-en-de",
        "tts": "de"
    }
}


# ==========================================
# Load Translation Model
# ==========================================

@lru_cache(maxsize=4)
def get_translator(language_code):

    model_name = LANGUAGES[language_code]["model"]

    print("\n========================================")
    print(f"Loading translation model: {model_name}")
    print("========================================")

    tokenizer = MarianTokenizer.from_pretrained(
        model_name
    )

    model = MarianMTModel.from_pretrained(
        model_name
    )

    print("Translation model loaded successfully!")

    return tokenizer, model


# ==========================================
# Translate Text
# ==========================================

def translate_text(text, language_code):

    tokenizer, model = get_translator(language_code)

    # Convert English text into model input
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True
    )

    # Generate translation
    translated = model.generate(
        **inputs,
        max_length=512
    )

    # Convert model output into text
    translated_text = tokenizer.decode(
        translated[0],
        skip_special_tokens=True
    )

    return translated_text


# ==========================================
# Home Route
# ==========================================

@app.route("/", methods=["GET", "POST"])
def home():

    translated_text = None
    audio_file = None

    text = ""
    language = ""
    language_name = ""
    language_flag = ""

    error_message = None

    # --------------------------------------
    # Handle POST Request
    # --------------------------------------

    if request.method == "POST":

        text = request.form.get(
            "text",
            ""
        ).strip()

        language = request.form.get(
            "language",
            ""
        ).strip()

        # ----------------------------------
        # Validate Text
        # ----------------------------------

        if not text:

            error_message = (
                "Please enter some English text."
            )

        # ----------------------------------
        # Validate Language
        # ----------------------------------

        elif language not in LANGUAGES:

            error_message = (
                "Please select a valid target language."
            )

        else:

            try:

                # ----------------------------------
                # Get Language Information
                # ----------------------------------

                language_info = LANGUAGES[language]

                language_name = language_info["name"]

                language_flag = language_info["flag"]

                # ----------------------------------
                # Translation
                # ----------------------------------

                print("\n========================================")
                print("Translating text...")
                print("========================================")

                translated_text = translate_text(
                    text,
                    language
                )

                print(
                    f"Translated Text: {translated_text}"
                )

                print("Translation completed!")

                # ----------------------------------
                # Text To Speech
                # ----------------------------------

                print("\nGenerating speech...")

                filename = (
                    f"echolang_{uuid.uuid4().hex}.mp3"
                )

                filepath = AUDIO_DIR / filename

                speech = gTTS(
                    text=translated_text,
                    lang=language_info["tts"],
                    slow=False
                )

                speech.save(
                    str(filepath)
                )

                # Browser uses this path
                audio_file = f"audio/{filename}"

                print("Audio generated successfully!")

                print(
                    f"Audio file: {filepath}"
                )

            except Exception as e:

                # ----------------------------------
                # Error Handling
                # ----------------------------------

                print("\n========================================")
                print("ERROR")
                print("========================================")

                print(
                    type(e).__name__,
                    ":",
                    str(e)
                )

                print("========================================")

                error_message = (
                    "Something went wrong while "
                    "processing your request. "
                    "Please try again."
                )


    # --------------------------------------
    # Render HTML
    # --------------------------------------

    return render_template(
        "index.html",

        translated_text=translated_text,

        audio_file=audio_file,

        text=text,

        language=language,

        language_name=language_name,

        language_flag=language_flag,

        error_message=error_message
    )


# ==========================================
# Run Application
# ==========================================

if __name__ == "__main__":

    print("\n========================================")
    print("       EchoLang - Multilingual TTS")
    print("========================================")

    print(f"Project folder : {BASE_DIR}")
    print(f"Audio folder   : {AUDIO_DIR}")

    print(
        "Audio folder exists:",
        AUDIO_DIR.exists()
    )

    print(
        "Open in browser: http://127.0.0.1:5000"
    )

    print("========================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
