# Originally located at \\\\Mac\\Home\\Documents\\Software\\_Scripts\\open_in_safari.py"
# needs to be given writeability using command "chmod +x /Users/phobrla/Documents/Software/_Scripts/open_in_safari.py"
#!/usr/bin/env python3
import sys
import json
import subprocess

def main():
    try:
        # Read input from Chrome extension
        input_line = sys.stdin.read()
        message = json.loads(input_line)

        # Extract the URL from the message
        url = message.get("url")

        if url:
            # Open the URL using the URL protocol
            subprocess.run([
                "C:\\Windows\\System32\\rundll32.exe",
                "url.dll,FileProtocolHandler",
                url
            ])

        # Send success response
        send_response({"success": True})
    except Exception as e:
        send_response({"success": False, "error": str(e)})

def send_response(response):
    response_str = json.dumps(response)
    sys.stdout.write(response_str)
    sys.stdout.flush()

if __name__ == "__main__":
    main()