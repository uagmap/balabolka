from __future__ import annotations

import os
import io
import wave

import torch


def generate_tts_bytes(text: str) -> io.BytesIO:
	"""Generate TTS and return a BytesIO containing a WAV file (mono, 16-bit)."""
	device = torch.device('cpu')
	torch.set_num_threads(4)
	local_file = 'v4_ru.pt'
	if not os.path.isfile(local_file):
		torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', local_file)
	model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
	model.to(device)

	sample_rate = 8000
	speaker = 'baya'

	audio_tensor = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)
	audio_tensor = audio_tensor.cpu()
	int16_tensor = (audio_tensor * 32767.0).clamp_(-32768, 32767).to(torch.int16)
	raw_bytes = int16_tensor.numpy().tobytes()

	buffer = io.BytesIO()
	with wave.open(buffer, 'wb') as wf:
		wf.setnchannels(1)
		wf.setsampwidth(2)
		wf.setframerate(sample_rate)
		wf.writeframes(raw_bytes)
	buffer.seek(0)
	return buffer


def is_cyrillic_text(text: str) -> bool:
	"""Return True if the text looks like Russian/Cyrillic input suitable for the model."""
	import re
	if not text or not text.strip():
		return False
	contains_cyrillic = re.search(r"[А-Яа-яЁё]", text) is not None
	contains_latin = re.search(r"[A-Za-z]", text) is not None
	return contains_cyrillic and not contains_latin


