from flask import Flask, render_template, request
from transformers import MarianMTModel, MarianTokenizer
from gtts import gTTS
from pathlib import Path
from functools import lru_cache
import uuid
import os


# ==========================================
# Flask Application
# ==========================================

app = Flask(__name__)


# ==========================================
# Configuration
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

AUDIO_DIR = BASE_DIR / "static" / "audio"

# Create audio directory if it does not exist
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

    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True
    )

    translated = model.generate(
        **inputs,
        max_length=512
    )

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

    # ======================================
    # POST Request
    # ======================================

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
        # Validate Input
        # ----------------------------------

        if not text:

            error_message = (
                "Please enter some English text."
            )

        elif language not in LANGUAGES:

            error_message = (
                "Please select a valid target language."
            )

        else:

            try:

                language_info = LANGUAGES[language]

                language_name = language_info["name"]
                language_flag = language_info["flag"]

                # ==============================
                # Translation
                # ==============================

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

                # ==============================
                # Text To Speech
                # ==============================

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

                # Browser audio path
                audio_file = f"audio/{filename}"

                print("Audio generated successfully!")

                print(
                    f"Audio file: {filepath}"
                )

            except Exception as e:

                print("\n========================================")
                print("ERROR")
                print("========================================")

                print(
                    f"{type(e).__name__}: {str(e)}"
                )

                print("========================================")

                error_message = (
                    "Something went wrong while "
                    "processing your request. "
                    "Please try again."
                )

    # ======================================
    # Render Template
    # ======================================

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
# Health Check Route
# ==========================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "application": "EchoLang",
        "message": "EchoLang server is running"
    }


# ==========================================
# Application Entry Point
# ==========================================

if __name__ == "__main__":

    # Render provides PORT automatically.
    # Local machine uses 5000.

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print("\n========================================")
    print("       EchoLang - Multilingual TTS")
    print("========================================")

    print(f"Project folder : {BASE_DIR}")
    print(f"Audio folder   : {AUDIO_DIR}")
    print(f"Audio exists   : {AUDIO_DIR.exists()}")
    print(f"Running port   : {port}")

    print("========================================")
    print("Local URL: http://127.0.0.1:5000")
    print("Health URL: /health")
    print("========================================\n")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
