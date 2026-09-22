from flask import Flask, render_template, request
from deep_translator import GoogleTranslator
from gtts import gTTS
from pathlib import Path
import uuid
import os
import time


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


# =========================================================
# DIRECTORIES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

AUDIO_DIR = BASE_DIR / "static" / "audio"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# SUPPORTED LANGUAGES
# =========================================================

LANGUAGES = {
    "hi": {
        "name": "Hindi",
        "flag": "🇮🇳",
        "tts": "hi"
    },

    "es": {
        "name": "Spanish",
        "flag": "🇪🇸",
        "tts": "es"
    },

    "fr": {
        "name": "French",
        "flag": "🇫🇷",
        "tts": "fr"
    },

    "de": {
        "name": "German",
        "flag": "🇩🇪",
        "tts": "de"
    }
}


# =========================================================
# TRANSLATION
# =========================================================

def translate_text(text, language_code):

    if language_code not in LANGUAGES:
        raise ValueError("Unsupported language selected.")

    last_error = None

    for attempt in range(2):

        try:

            translator = GoogleTranslator(
                source="en",
                target=language_code
            )

            result = translator.translate(text)

            if not result:
                raise ValueError(
                    "Translation service returned an empty result."
                )

            return result

        except Exception as e:

            last_error = e

            if attempt == 0:
                time.sleep(1)

    raise RuntimeError(
        f"Translation failed: {str(last_error)}"
    )


# =========================================================
# TEXT TO SPEECH
# =========================================================

def generate_audio(text, language_code):

    if not text:
        raise ValueError("No translated text available.")

    if language_code not in LANGUAGES:
        raise ValueError("Unsupported TTS language.")

    filename = f"echolang_{uuid.uuid4().hex}.mp3"

    filepath = AUDIO_DIR / filename

    last_error = None

    for attempt in range(2):

        try:

            speech = gTTS(
                text=text,
                lang=LANGUAGES[language_code]["tts"],
                slow=False
            )

            speech.save(str(filepath))

            if not filepath.exists():
                raise RuntimeError(
                    "Audio file was not created."
                )

            if filepath.stat().st_size == 0:
                raise RuntimeError(
                    "Generated audio file is empty."
                )

            return filename

        except Exception as e:

            last_error = e

            try:
                if filepath.exists():
                    filepath.unlink()
            except Exception:
                pass

            if attempt == 0:
                time.sleep(1)

    raise RuntimeError(
        f"Text-to-speech failed: {str(last_error)}"
    )


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET", "POST"])
def home():

    translated_text = None
    audio_file = None

    text = ""
    language = ""
    language_name = ""
    language_flag = ""

    error_message = None

    if request.method == "POST":

        try:

            text = request.form.get(
                "text",
                ""
            ).strip()

            language = request.form.get(
                "language",
                ""
            ).strip()

            # -------------------------------------------------
            # VALIDATION
            # -------------------------------------------------

            if not text:

                error_message = (
                    "Please enter some English text."
                )

            elif len(text) > 3000:

                error_message = (
                    "Please keep the text below 3000 characters."
                )

            elif language not in LANGUAGES:

                error_message = (
                    "Please select a valid target language."
                )

            else:

                language_info = LANGUAGES[language]

                language_name = language_info["name"]
                language_flag = language_info["flag"]

                # -------------------------------------------------
                # TRANSLATION
                # -------------------------------------------------

                print()
                print("=" * 55)
                print("ECHOLANG - TRANSLATION")
                print("=" * 55)

                print(
                    f"Target Language : {language_name}"
                )

                print(
                    f"Input Text      : {text[:100]}"
                )

                translated_text = translate_text(
                    text,
                    language
                )

                print(
                    f"Translated Text : {translated_text}"
                )

                # -------------------------------------------------
                # TEXT TO SPEECH
                # -------------------------------------------------

                print("Generating speech...")

                filename = generate_audio(
                    translated_text,
                    language
                )

                audio_file = f"audio/{filename}"

                print(
                    f"Audio generated : {filename}"
                )

                print("=" * 55)
                print("REQUEST COMPLETED")
                print("=" * 55)

        except Exception as e:

            # -------------------------------------------------
            # IMPORTANT:
            # Never allow a normal application error to
            # crash the Flask request.
            # -------------------------------------------------

            print()
            print("=" * 55)
            print("ECHOLANG ERROR")
            print("=" * 55)

            print(
                f"Error Type : {type(e).__name__}"
            )

            print(
                f"Error      : {str(e)}"
            )

            print("=" * 55)

            translated_text = None
            audio_file = None

            error_message = (
                "Unable to process the request right now. "
                "Please try again."
            )

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


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "application": "EchoLang",
        "message": "EchoLang server is running"
    }, 200


# =========================================================
# ERROR HANDLERS
# =========================================================

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
        error_message=(
            "The submitted text is too large. "
            "Please use a shorter text."
        )
    ), 413


@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "index.html",
        translated_text=None,
        audio_file=None,
        text="",
        language="",
        language_name="",
        language_flag="",
        error_message="The requested page was not found."
    ), 404


@app.errorhandler(500)
def internal_server_error(error):

    print(
        f"Internal server error: {error}"
    )

    return render_template(
        "index.html",
        translated_text=None,
        audio_file=None,
        text="",
        language="",
        language_name="",
        language_flag="",
        error_message=(
            "Something went wrong. "
            "Please try again."
        )
    ), 500


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print()
    print("=" * 55)
    print("ECHOLANG - MULTILINGUAL TEXT TO SPEECH")
    print("=" * 55)

    print(
        f"Project Folder : {BASE_DIR}"
    )

    print(
        f"Audio Folder   : {AUDIO_DIR}"
    )

    print(
        f"Port           : {port}"
    )

    print("=" * 55)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
