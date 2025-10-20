from __future__ import annotations

import os
import io
import wave

import torch

AVAILABLE_VOICES = ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']

_model_cache = None
def _load_model():
	"""load and cache TTS model"""
	# This used to be part of generate_tts_bytes, but was moved to a separate function to avoid reloading
	# the model every time for generating for each voice
	
	#check if already loaded
	global _model_cache
	if _model_cache is not None:
		return _model_cache

	device = torch.device('cpu')
	torch.set_num_threads(4)
	local_file = 'v4_ru.pt'
	if not os.path.isfile(local_file):
		torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', local_file)
	model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
	model.to(device)
	_model_cache = model
	return model

def generate_tts_bytes(text: str, speaker: str) -> io.BytesIO:
	"""Generate TTS and return a BytesIO containing a WAV file (mono, 16-bit)."""
	model = _load_model()
	sample_rate = 8000

	audio_tensor = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)
	audio_tensor = audio_tensor.cpu()
	# Convert (-1.0, 1.0) float audio range to 16-bit signed, clamp to this range and convert to torch int
	int16_tensor = (audio_tensor * 32767.0).clamp_(-32768, 32767).to(torch.int16)
	# PyTorch tensor to numpy array and to raw bytes
	raw_bytes = int16_tensor.numpy().tobytes()

	# WAV file creation
	buffer = io.BytesIO()
	with wave.open(buffer, 'wb') as wf:
		wf.setnchannels(1)
		wf.setsampwidth(2)
		wf.setframerate(sample_rate)
		wf.writeframes(raw_bytes)
	buffer.seek(0)
	return buffer

def generate_all_voices(text: str) -> dict[str, io.BytesIO]:
	result = {}
	for voice in AVAILABLE_VOICES:
		result[voice] = generate_tts_bytes(text, voice)
	return result

def is_cyrillic_text(text: str) -> bool:
	"""Return True if the text looks like Russian/Cyrillic input suitable for the model."""
	import re
	if not text or not text.strip():
		return False
	contains_cyrillic = re.search(r"[А-Яа-яЁё]", text) is not None
	contains_latin = re.search(r"[A-Za-z]", text) is not None
	return contains_cyrillic and not contains_latin


