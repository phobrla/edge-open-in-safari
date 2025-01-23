# Open in Safari

This project provides a way to open URLs in Safari from other browsers using a native messaging host.

## Description

The `open_in_safari` script allows users to open URLs directly in Safari from other browsers like Chrome and Edge using a native messaging host.

## Configuration

### Native Messaging Host Configuration

Create a JSON configuration file to register the native messaging host with your browser. Below is an example configuration:

```json
{
    "_comment": "Originally located at \\\\Mac\\Home\\Library\\Application Support\\Microsoft Edge\\NativeMessagingHosts\\com.cupofjune.open_in_safari.json; create using mkdir -p ~\/Library/Application\\ Support/Microsoft\\ Edge\\ NativeMessagingHosts\/"
    "name": "com.cupofjune.openinsafari",
    "description": "Open URLs in Safari",
    "path": "/Users/phobrla/Documents/Software/_Scripts/open_in_safari.py",
    "type": "stdio",
    "allowed_origins": [
        "chrome-extension://blejmdndaoijjaleenahpjdhkimhkmbf/"
    ]
}
```

### Script

The `open_in_safari.py` script should be located at the path specified in the configuration file and should be executable. Below is a sample script:

```python
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
            # Open the URL in Safari
            subprocess.run(["open", "-a", "Safari", url])

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
```

## Usage

To use this native messaging host, you need to implement a browser extension that sends a message with a URL to the native messaging host.

### Browser Extension Example

```javascript
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "openInSafari" && request.url) {
        chrome.runtime.sendNativeMessage(
            'com.cupofjune.openinsafari',
            { url: request.url },
            function(response) {
                console.log("Response from native app:", response);
            }
        );
    }
});
```

## Languages Used

- Python (35.7%)
- JavaScript (31.1%)
- HTML (19.1%)
- Batchfile (14.1%)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```
