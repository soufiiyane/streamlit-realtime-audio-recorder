# Streamlit Realtime Audio Recorder

A Streamlit component that records audio in real-time and automatically stops recording after a configurable silence period.

## Installation

```bash
pip install streamlit-realtime-audio-recorder
```

## Usage

```python
from streamlit_realtime_audio_recorder import audio_recorder
import streamlit as st
import base64
import io

result = audio_recorder(
    interval=50,
    threshold=-60,
    silenceTimeout=200
)

if result:
    if result.get('status') == 'stopped':
        audio_data = result.get('audioData')
        if audio_data:
            audio_bytes = base64.b64decode(audio_data)
            audio_file = io.BytesIO(audio_bytes)
            st.audio(audio_file, format="audio/webm")
        else:
            pass
    elif result.get('error'):
            st.error(f"Error: {result.get('error')}")
```

## Parameters

- `interval` (optional, default: 50): How often to check audio level in milliseconds
- `threshold` (optional, default: -60): Audio level threshold for speech detection in dB
- `silenceTimeout` (optional, default: 1500): Time in milliseconds to wait after silence before stopping recording
- `play` (optional, default: False): Whether to play the audio during recording

# Demo

<table>
<tr>
<td width="50%">
<h3>🎤 Streamlit Realtime Audio Recorder</h3>
<p>Real-time audio recording directly in your Streamlit app.</p>
<video width="100%" controls>
  <source src="https://github.com/soufiiyane/streamlit-realtime-audio-recorder/raw/main/demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
</td>
</tr>
</table>


## How It Works

This component uses the Web Audio API and the hark library to detect speech and silence. When you click the microphone button:

1. The microphone starts recording
2. When you stop speaking (silence is detected), the recording automatically stops after a configurable timeout
3. The audio data is returned as base64-encoded data that you can play, save, or process

## Use Cases

- Voice commands in Streamlit apps
- Speech-to-text integration
- Audio data collection
- Voice recording with automatic silence detection

## License

MIT