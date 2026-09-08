# 🎙️ EchoLang - Multilingual Text-to-Speech

EchoLang is a web-based **Multilingual Text-to-Speech (TTS)** application built using **Python, Flask, Hugging Face Transformers, MarianMT, and Google Text-to-Speech (gTTS)**.

The application accepts English text, translates it into a selected language, and converts the translated text into speech.

---

## 🌍 Supported Languages

Currently, EchoLang supports the following languages:

| Language | Flag | Translation Model | TTS |
|----------|------|-------------------|-----|
| Hindi | 🇮🇳 | Helsinki-NLP/opus-mt-en-hi | hi |
| Spanish | 🇪🇸 | Helsinki-NLP/opus-mt-en-es | es |
| French | 🇫🇷 | Helsinki-NLP/opus-mt-en-fr | fr |
| German | 🇩🇪 | Helsinki-NLP/opus-mt-en-de | de |

---

## ✨ Features

- 📝 Enter English text
- 🌍 Translate English text into multiple languages
- 🤖 Uses Hugging Face MarianMT translation models
- 🔊 Converts translated text into speech
- 🎧 Generates MP3 audio files
- ⚡ Flask-based web application
- 💾 Automatically stores generated audio files
- 🧠 Translation models are cached for better performance
- 🎨 Simple and user-friendly web interface

---

## 🛠️ Technologies Used

### Backend

- Python
- Flask
- Hugging Face Transformers
- MarianMT
- PyTorch
- gTTS

### Frontend

- HTML
- CSS
- JavaScript

### Other Libraries

- pathlib
- functools
- uuid

---

## 📁 Project Structure

```text
EchoLang-TTS/
│
├── app.py
│
├── static/
│   ├── audio/
│   └── style.css
│
├── templates/
│   └── index.html
│
├── .gitignore
├── README.md
└── requirements.txt
