import json
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

# एडमिन रिमोट सेटिंग्स (फुल कंट्रोल आपके हाथ में)
ADMIN_SETTINGS = {
    "app_name": "Nexus AI",
    "chat_enabled": True,
    "image_enabled": True,
    "video_enabled": True,
    "maintenance_mode": False
}

class NexusServer(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, secret-token')
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"status": "Running", "app_name": ADMIN_SETTINGS["app_name"]}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404, "Route Not Found")

    def do_POST(self):
        global ADMIN_SETTINGS
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}

        if ADMIN_SETTINGS["maintenance_mode"] and self.path != "/api/admin/control":
            self.send_json_response(503, {"detail": "App is under maintenance by Admin."})
            return

        # A. ऑल-इन-वन चैट असिस्टेंट रूट
        if self.path == "/api/chat":
            if not ADMIN_SETTINGS["chat_enabled"]:
                self.send_json_response(403, {"detail": "Chat feature is disabled by Admin."})
                return
            
            api_key = data.get("api_key")
            message = data.get("message")
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": message}]}]}
                res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
                ai_reply = res.json()['candidates'][0]['content']['parts'][0]['text']
                self.send_json_response(200, {"response": ai_reply})
            except Exception as e:
                self.send_json_response(400, {"detail": f"Nexus Engine Error: {str(e)}"})

        # B. इमेज जनरेटर रूट
        elif self.path == "/api/generate-image":
            if not ADMIN_SETTINGS["image_enabled"]:
                self.send_json_response(403, {"detail": "Image Generation is disabled by Admin."})
                return
            prompt = data.get("prompt", "").replace(" ", "%20")
            image_url = f"https://image.pollinations.ai/p/{prompt}?width=1080&height=1080&nologo=true"
            self.send_json_response(200, {"image_url": image_url})

        # C. वीडियो जनरेटर रूट (2 मिनट सपोर्ट)
        elif self.path == "/api/generate-video":
            if not ADMIN_SETTINGS["video_enabled"]:
                self.send_json_response(403, {"detail": "Video Generation is disabled by Admin."})
                return
            prompt = data.get("prompt", "").replace(" ", "%20")
            style = data.get("style", "HD%20Cinematic")
            video_url = f"https://textto-video.pollinations.ai/{prompt}&style={style}&duration=120"
            self.send_json_response(200, {"video_url": video_url, "max_duration": "2 Minutes"})

        # D. खुफिया एडमिन कंट्रोल पैनल
        elif self.path == "/api/admin/control":
            secret_token = self.headers.get('secret-token')
            if secret_token != "RounakNexusAdmin2026":
                self.send_json_response(401, {"detail": "Unauthorized Access!"})
                return
            ADMIN_SETTINGS.update(data)
            self.send_json_response(200, {"message": "Nexus AI updated successfully!", "current_settings": ADMIN_SETTINGS})

        else:
            self.send_error(404, "Route Not Found")

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == "__main__":
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, NexusServer)
    print("🚀 Nexus Engine Live!")
    httpd.serve_forever()

