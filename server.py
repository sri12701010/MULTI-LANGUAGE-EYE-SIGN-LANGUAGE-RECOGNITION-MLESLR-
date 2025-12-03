from flask import Flask, Response, render_template_string
import time

app = Flask(__name__)
latest_output = "Waiting for output..."

@app.route('/')
def index():
    return render_template_string("""
        <!doctype html>
        <html>
        <head>
            <title>Live Output with Voice</title>
            <style>
                body {
                    background-color: #121212;
                    color: #FFFFFF;
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin-top: 80px;
                }
                #output {
                    font-size: 6em;
                    font-weight: bold;
                    color: #00ffcc;
                    margin-top: 40px;
                }
                button {
                    font-size: 1.2em;
                    padding: 10px 20px;
                    margin-top: 30px;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <h1>Live Translated Output:</h1>
            <div id="output">Waiting for output...</div>
            <button onclick="enableTTS()">🔊 Enable Voice</button>

            <script>
                let ttsEnabled = false;
                let previousText = "";

                function enableTTS() {
                    ttsEnabled = true;
                    speak("Voice enabled. Waiting for message.");
                }

                function speak(text) {
                    if (!ttsEnabled) return;
                    const msg = new SpeechSynthesisUtterance(text);
                    msg.lang = 'en'; // Use 'hi' or 'te' for Hindi/Telugu
                    window.speechSynthesis.cancel();  // Stop previous speech
                    window.speechSynthesis.speak(msg);
                }

                const source = new EventSource("/stream");
                source.onmessage = function(event) {
                    const currentText = event.data;
                    if (currentText !== previousText) {
                        document.getElementById("output").innerHTML = currentText;
                        speak(currentText);
                        previousText = currentText;
                    }
                };
            </script>
        </body>
        </html>
    """)

@app.route('/stream')
def stream():
    def event_stream():
        previous_output = ""
        while True:
            if latest_output != previous_output:
                yield f"data: {latest_output}\n\n"
                previous_output = latest_output
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

def update_output(new_output):
    global latest_output
    latest_output = new_output

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
