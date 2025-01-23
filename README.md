# Open in Safari

This project provides a way to open URLs in Safari from other browsers using a native messaging host.

## Description

The `open_in_safari` script allows users to open URLs directly in Safari from other browsers like Chrome and Edge using a native messaging host.

## Configuration

### Native Messaging Host Configuration

Create a JSON configuration file to register the native messaging host with your browser. Below is an example configuration:

```json
{
    "name": "com.cupofjune.openinsafari",
    "description": "Open URLs in Safari",
    "path": "/Users/phobrla/Documents/Software/_Scripts/open_in_safari.py",
    "type": "stdio",
    "allowed_origins": [
        "chrome-extension://blejmdndaoijjaleenahpjdhkimhkmbf/"
    ],
    "_comment": "Located at \\\\Mac\\Home\\Library\\Application Support\\Microsoft Edge\\NativeMessagingHosts\\com.cupofjune.open_in_safari.json"
}
```

### Script

The `open_in_safari.py` script should be located at the path specified in the configuration file and should be executable. Below is a sample script:

```python
import sys
import json
import subprocess

def open_in_safari(url):
    subprocess.run(["open", "-a", "Safari", url])

def main():
    input_stream = sys.stdin.read()
    message = json.loads(input_stream)
    url = message.get("url")
    
    if url:
        open_in_safari(url)
    else:
        print("No URL provided", file=sys.stderr)

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
