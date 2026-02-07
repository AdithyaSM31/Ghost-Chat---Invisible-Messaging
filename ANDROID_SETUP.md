# Building Android APK with Capacitor

Since your project uses a Python backend, the Android app will act as a **client** that connects to your computer (where the server is running). The app itself cannot run the Python code offline.

## **Step 1: Configure IP Address**
1.  Open Command Prompt on your computer and run:
    ```bash
    ipconfig
    ```
2.  Find your **IPv4 Address** (e.g., `192.168.1.10`).
3.  Open the file `capacitor.config.json` in this project.
4.  Replace `192.168.X.X` with your actual IP address:
    ```json
    "server": {
      "url": "http://192.168.1.10:5000",
      "cleartext": true
    }
    ```

## **Step 2: Start the Backend**
You must have the Flask server running for the app to work.
```bash
python web_app.py
```
*Note: Ensure your firewall allows incoming connections on port 5000.*

## **Step 3: Open in Android Studio**
1.  Run this command in the terminal:
    ```bash
    npx cap open android
    ```
2.  This will launch Android Studio.
3.  Wait for Gradle sync to finish.
4.  Connect your Android phone (Enable USB Debugging) or use the Emulator.
5.  Click the **Play/Run** button (green triangle).

## **Troubleshooting**
- **White Screen?** Ensure your phone and laptop are on the same Wi-Fi.
- **Connection Refused?** Check your specific IP address again.
- **Backend Offline?** The app will stop working if you close `python web_app.py`.
