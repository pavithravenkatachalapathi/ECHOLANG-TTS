from flask import Flask, render_template, request
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from gtts import gTTS
from pathlib import Path
from functools import lru_cache
import uuid
import os
import gc


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# Reduce memory overhead: cap torch's internal thread pool (each thread
# allocates its own working buffers, which adds up on low-RAM hosts).
torch.set_num_threads(1)

# Maximum text size: 5000 characters
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

AUDIO_DIR = BASE_DIR / "static" / "audio"

# Create audio directory automatically
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

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


# ============================================================
# LOAD TRANSLATION MODEL
# ============================================================

@lru_cache(maxsize=1)
def get_translator(language_code):

    if language_code not in LANGUAGES:
        raise ValueError("Unsupported language")

    model_name = LANGUAGES[language_code]["model"]

    print("=" * 60)
    print(f"Loading model: {model_name}")
    print("=" * 60)

    tokenizer = AutoTokenizer.from_pretrained(
        model_name
    )

    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        low_cpu_mem_usage=True
    )

    # Evaluation mode
    model.eval()

    print("Model loaded successfully.")
    print("=" * 60)

    return tokenizer, model


# ============================================================
# TRANSLATION FUNCTION
# ============================================================

def translate_text(text, language_code):

    tokenizer, model = get_translator(language_code)

    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    )

    with torch.no_grad():
        generated_tokens = model.generate(
            **inputs,
            max_length=512,
            num_beams=1
        )

    translated_text = tokenizer.decode(
        generated_tokens[0],
        skip_special_tokens=True
    )

    del inputs, generated_tokens
    gc.collect()

    return translated_text.strip()


# ============================================================
# TEXT TO SPEECH
# ============================================================

def generate_audio(text, language_code):

    filename = f"echolang_{uuid.uuid4().hex}.mp3"

    filepath = AUDIO_DIR / filename

    speech = gTTS(
        text=text,
        lang=language_code,
        slow=False
    )

    speech.save(str(filepath))

    return f"audio/{filename}"


# ============================================================
# HOME ROUTE
# ============================================================

@app.route("/", methods=["GET", "POST"])
def home():

    translated_text = None
    audio_file = None

    text = ""
    language = ""

    language_name = ""
    language_flag = ""

    error_message = None

    # --------------------------------------------------------
    # POST REQUEST
    # --------------------------------------------------------

    if request.method == "POST":

        text = request.form.get(
            "text",
            ""
        ).strip()

        language = request.form.get(
            "language",
            ""
        ).strip()

        # ----------------------------------------------------
        # INPUT VALIDATION
        # ----------------------------------------------------

        if not text:

            error_message = (
                "Please enter some English text."
            )

        elif language not in LANGUAGES:

            error_message = (
                "Please select a valid target language."
            )

        else:

            language_info = LANGUAGES[language]

            language_name = language_info["name"]
            language_flag = language_info["flag"]

            # ------------------------------------------------
            # TRANSLATION
            # ------------------------------------------------

            try:

                print("=" * 60)
                print("Translation started")
                print(f"Target language: {language_name}")
                print(f"Input: {text}")
                print("=" * 60)

                translated_text = translate_text(
                    text,
                    language
                )

                print(
                    f"Translation: {translated_text}"
                )

                print("Translation completed.")

            except Exception as e:

                print("=" * 60)
                print("TRANSLATION ERROR")
                print(type(e).__name__)
                print(str(e))
                print("=" * 60)

                error_message = (
                    "Translation could not be completed. "
                    "Please try again."
                )

            # ------------------------------------------------
            # TEXT TO SPEECH
            # ------------------------------------------------

            if translated_text:

                try:

                    print("=" * 60)
                    print("Generating speech...")
                    print("=" * 60)

                    audio_file = generate_audio(
                        translated_text,
                        language_info["tts"]
                    )

                    print(
                        f"Audio generated: {audio_file}"
                    )

                except Exception as e:

                    print("=" * 60)
                    print("TTS ERROR")
                    print(type(e).__name__)
                    print(str(e))
                    print("=" * 60)

                    # TTS failure should NOT destroy
                    # the translation result.
                    audio_file = None


    # ========================================================
    # RENDER PAGE
    # ========================================================

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


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    return {
        "status": "ok",
        "application": "EchoLang",
        "message": "EchoLang server is running"
    }, 200


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(413)
def request_too_large(error):

    return render_template(
        "index.html",
        translated_text=None,
        audio_file=None,
        text="",
        language="",
        language_name="",
        language_flag="",
        error_message="Text is too large. Please enter a shorter text."
    ), 413


@app.errorhandler(500)
def internal_server_error(error):

    print("=" * 60)
    print("INTERNAL SERVER ERROR")
    print(str(error))
    print("=" * 60)

    return render_template(
        "index.html",
        translated_text=None,
        audio_file=None,
        text="",
        language="",
        language_name="",
        language_flag="",
        error_message="Something went wrong. Please try again."
    ), 500


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print("=" * 60)
    print("             ECHOLANG")
    print("     Multilingual Translation + TTS")
    print("=" * 60)

    print(f"Project directory : {BASE_DIR}")
    print(f"Audio directory   : {AUDIO_DIR}")
    print(f"Audio exists      : {AUDIO_DIR.exists()}")
    print(f"Port              : {port}")

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
