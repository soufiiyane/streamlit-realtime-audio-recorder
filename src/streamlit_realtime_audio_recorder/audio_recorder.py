import streamlit as st
import os
import tempfile
import streamlit.components.v1 as components
import base64

def gencomponent(name, template="", script=""):
    def html():
        return f"""
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8" />
                    <title>{name}</title>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" integrity="sha512-Evv84Mr4kqVGRNSgIGL/F/aIDqQb7xQ2vcrdIwxfjThSH8CSR7PBEakCr51Ck+w+/U6swU2Im1vVX0SVk9ABhg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
                    <style>
                        body {{
                            background-color: transparent;
                            margin: 0;
                            padding: 0;
                        }}
                        #toggleBtn {{
                            padding: 10px 20px;
                            border-radius: 4px;
                            border: none;
                            cursor: pointer;
                            color: #282828;
                            font-size: 16px;
                        }}
                        #toggleBtn.recording {{
                            background-color: red;
                        }}
                    </style>
                    <script>
                        function sendMessageToStreamlitClient(type, data) {{
                            const outData = Object.assign({{
                                isStreamlitMessage: true,
                                type: type,
                            }}, data);
                            window.parent.postMessage(outData, "*");
                        }}

                        const Streamlit = {{
                            setComponentReady: function() {{
                                sendMessageToStreamlitClient("streamlit:componentReady", {{apiVersion: 1}});
                            }},
                            setFrameHeight: function(height) {{
                                sendMessageToStreamlitClient("streamlit:setFrameHeight", {{height: height}});
                            }},
                            setComponentValue: function(value) {{
                                sendMessageToStreamlitClient("streamlit:setComponentValue", {{value: value}});
                            }},
                            RENDER_EVENT: "streamlit:render",
                            events: {{
                                addEventListener: function(type, callback) {{
                                    window.addEventListener("message", function(event) {{
                                        if (event.data.type === type) {{
                                            event.detail = event.data
                                            callback(event);
                                        }}
                                    }});
                                }}
                            }}
                        }}
                    </script>
                </head>
                <body>
                    {template}
                </body>
                <script src="https://unpkg.com/hark@1.2.0/hark.bundle.js"></script>
                <script>
                    {script}
                </script>
            </html>
        """

    dir = f"{tempfile.gettempdir()}/{name}"
    if not os.path.isdir(dir): os.mkdir(dir)
    fname = f'{dir}/index.html'
    f = open(fname, 'w')
    f.write(html())
    f.close()
    func = components.declare_component(name, path=str(dir))
    def f(**params):
        component_value = func(**params)
        return component_value
    return f

template = """
    <button id="toggleBtn"><i class="fa-solid fa-microphone fa-lg" ></i></button>
"""

script = """
    let mediaStream = null;
    let mediaRecorder = null;
    let audioChunks = [];
    let speechEvents = null;
    let silenceTimeout = null;
    let isRecording = false;
    const toggleBtn = document.getElementById('toggleBtn');
    
    Streamlit.setComponentReady();
    Streamlit.setFrameHeight(60);
    
    function blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64String = reader.result.split(',')[1];
                resolve(base64String);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    async function handleRecordingStopped() {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const base64Data = await blobToBase64(audioBlob);
        
        Streamlit.setComponentValue({
            audioData: base64Data,
            status: 'stopped'
        });
    }
    
    function onRender(event) {
        const args = event.detail.args;
        window.harkConfig = {
            interval: args.interval || 50,
            threshold: args.threshold || -60,
            play: args.play !== undefined ? args.play : false,
            silenceTimeout: args.silenceTimeout || 1500
        };
        
        console.log("Hark configuration:", window.harkConfig);
    }
    
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
    
    toggleBtn.addEventListener('click', async () => {
        if (!isRecording) {
            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(mediaStream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = () => {
                    handleRecordingStopped().catch(err => {
                        console.error('Error handling recording:', err);
                        Streamlit.setComponentValue({
                            error: 'Failed to process recording'
                        });
                    });
                };
                
                speechEvents = hark(mediaStream, {
                    interval: window.harkConfig.interval,
                    threshold: window.harkConfig.threshold,
                    play: window.harkConfig.play
                });
                
                speechEvents.on('stopped_speaking', () => {
                    silenceTimeout = setTimeout(() => {
                        if (mediaRecorder && mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();
                            
                            if (isRecording) {
                                audioChunks = [];
                                mediaRecorder = new MediaRecorder(mediaStream);
                                mediaRecorder.ondataavailable = event => {
                                    if (event.data.size > 0) {
                                        audioChunks.push(event.data);
                                    }
                                };
                                mediaRecorder.onstop = () => {
                                    handleRecordingStopped().catch(err => {
                                        console.error('Error handling recording:', err);
                                    });
                                };
                                mediaRecorder.start();
                            }
                        }
                    }, window.harkConfig.silenceTimeout);
                });
                
                speechEvents.on('speaking', () => {
                    if (silenceTimeout) {
                        clearTimeout(silenceTimeout);
                        silenceTimeout = null;
                    }
                });
                
                mediaRecorder.start();
                isRecording = true;
                toggleBtn.classList.add('recording');
                
            } catch (err) {
                console.error('Error accessing microphone:', err);
                Streamlit.setComponentValue({
                    error: err.message
                });
            }
        } else {
            isRecording = false;
            toggleBtn.classList.remove('recording');
            
            if (speechEvents) {
                speechEvents.stop();
                speechEvents = null;
            }
            
            if (silenceTimeout) {
                clearTimeout(silenceTimeout);
                silenceTimeout = null;
            }
            
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
            }
            
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
        }
    });
"""

def audio_recorder(interval=50, threshold=-60, play=False, silenceTimeout=1500):
    """
    Create a streamlit component for recording audio with silence detection.
    
    Parameters:
    -----------
    interval: int, optional (default=50)
        How often to check audio level in milliseconds
    threshold: int, optional (default=-60)
        Audio level threshold for speech detection in dB
    play: bool, optional (default=False)
        Whether to play the audio during recording
    silenceTimeout: int, optional (default=1500)
        Time in milliseconds to wait after silence before stopping recording
        
    Returns:
    --------
    dict or None
        A dictionary containing:
        - audioData: base64 encoded audio data (if recording was successful)
        - status: recording status (e.g. 'stopped')
        - error: error message (if an error occurred)
        Returns None if the component has not been interacted with
    """
    component_func = gencomponent('configurable_audio_recorder', template=template, script=script)
    return component_func(interval=interval, threshold=threshold, play=play, silenceTimeout=silenceTimeout)