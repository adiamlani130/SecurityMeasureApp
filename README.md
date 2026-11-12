# SecurityMeasureApp

SecurityMeasureApp is an IoT security and monitoring application for the **Raspberry Pi 400**. It combines environmental sensors, motion detection, a webcam and AWS cloud services to detect fire, gas/smoke, intruders, water and extreme temperatures, and texts the owner a summary with a link to a short security video.

> This project is for educational and demonstration purposes. It is **not** a certified safety or security system.

## Features

- **Fire and smoke detection**: MQ-2 gas sensor and flame sensor
- **Environmental monitoring**: DHT11 temperature and humidity sensor, rain/water sensor, local weather from the free [Open-Meteo](https://open-meteo.com/) API
- **Intrusion detection**: HC-SR501 PIR motion sensor
- **Status indicators**: KY-008 laser is on while the system is armed; optional LED per sensor
- **Two-factor identity verification** before arming:
  - face match against the owner's photo with **AWS Rekognition**
  - spoken pass-phrase recorded from the microphone and checked with **AWS Transcribe**
- **Threat assessment and alerts**:
  - sensors are polled every 5 seconds
  - a simple scoring rule rates urgency LOW / MEDIUM / HIGH
  - a small linear-regression model estimates the expected financial loss
  - on an alert the webcam records a 5 second clip to a **private S3 bucket**, and an SMS with the summary, a temporary video link and the weather is sent through **AWS SNS**
  - alerts are rate-limited (default: at most one every 2 minutes)

## How it works

```
main.py (Tkinter GUI)
 ├─ Voice button ──► verification.py: arecord ─► S3 ─► Transcribe ─► pass-phrase check
 ├─ Face button ───► verification.py: webcam photo ─► Rekognition CompareFaces
 ├─ Arm button (appears after both pass)
 │    └─ background thread, every 5 s:
 │         sensorDetection.py: read GPIO sensors + DHT11, update LEDs
 │           └─ response.py: score threat ─► record video ─► S3 (presigned link)
 │                 └─ sendMessage.py: SNS SMS (+ weatherInformation.py summary)
 └─ Clock + weather panel (weatherInformation.py, Open-Meteo)
```

## Hardware

| Part | Notes |
|---|---|
| Raspberry Pi 400 | Raspberry Pi OS (Bookworm or Bullseye) with desktop |
| MQ-2 gas sensor module | digital output (DO) used |
| Flame sensor module | digital output (DO) used |
| DHT11 temperature/humidity sensor | 3-pin module, or bare sensor plus a 10 kΩ pull-up |
| Rain/water sensor module | digital output (DO) used |
| HC-SR501 PIR motion sensor | |
| KY-008 laser module | armed indicator |
| LEDs + 220–330 Ω resistors | optional, one per sensor |
| USB webcam | used for the face photo and alarm video |
| USB microphone (or a webcam with a mic) | used for the voice pass-phrase |
| Breadboard, jumper wires | |

### Wiring (default pins)

Pins use **BCM numbering** (the `GPIOxx` names, not the physical header position). Every pin can be changed in `config.py` or with an environment variable.

| Sensor | Module pin | Pi pin (BCM) | Physical pin | Setting |
|---|---|---|---|---|
| DHT11 | DATA | GPIO4 | 7 | `DHT_PIN` |
| MQ-2 | DO | GPIO17 | 11 | `GAS_PIN` |
| Flame sensor | DO | GPIO27 | 13 | `FLAME_PIN` |
| HC-SR501 PIR | OUT | GPIO22 | 15 | `MOTION_PIN` |
| Rain sensor | DO | GPIO23 | 16 | `RAIN_PIN` |
| KY-008 laser | S | GPIO24 | 18 | `LASER_PIN` |
| LEDs (optional) | anode via resistor | any free GPIO | | `GAS_LED_PIN`, `FLAME_LED_PIN`, `MOTION_LED_PIN`, `RAIN_LED_PIN` |

Connect every module's GND to a Pi GND pin (e.g. physical pin 6).

> ⚠️ **The Pi's GPIO pins take 3.3 V only.** The MQ-2's heater needs 5 V, and many flame and rain boards are powered at 5 V too. If a module is powered from 5 V, its DO pin can output 5 V and damage the Pi. Either power the module from 3.3 V (if it works at that voltage), or put a voltage divider (e.g. 10 kΩ / 20 kΩ) or a level shifter between DO and the GPIO pin. The HC-SR501 runs on 5 V but its output is 3.3 V, so it is safe.

**Active-low outputs:** most MQ-2, flame and rain boards pull DO **low** when they detect something, while the PIR drives its output **high**. Those are the defaults (`GAS_ACTIVE_LOW`, `FLAME_ACTIVE_LOW`, `RAIN_ACTIVE_LOW` = true; `MOTION_ACTIVE_LOW` = false). If a sensor reads "detected" when nothing is there, flip its setting. Use the potentiometer on the MQ-2, flame and rain boards to set their trigger threshold.

## Software setup

### 1. System packages

```bash
sudo apt update
```

```bash
sudo apt install -y python3-venv python3-tk libgpiod2 alsa-utils
```

- `python3-tk` provides Tkinter for the GUI.
- `libgpiod2` is used by the DHT11 driver.
- `alsa-utils` provides `arecord`, which records the voice pass-phrase. It is normally preinstalled.

### 2. Python environment

Recent Raspberry Pi OS versions block system-wide `pip install`, so use a virtual environment:

```bash
cd SecurityMeasureApp
```

```bash
python3 -m venv --system-site-packages .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

If `opencv-python` fails to install on your Pi, run `sudo apt install python3-opencv` instead. The `--system-site-packages` venv will pick it up.

### 3. Check the camera and microphone

```bash
arecord -l
```

```bash
arecord -d 3 -f S16_LE -r 16000 -c 1 test.wav && aplay test.wav
```

If the microphone is not the default device, set `AUDIO_DEVICE`, e.g. `export AUDIO_DEVICE=plughw:1,0`. If the webcam is not camera 0, set `CAMERA_INDEX`.

## AWS setup

1. **Credentials:** create an IAM user for the Pi and run `aws configure` on the Pi (or set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`). Never put keys in the code.
2. **Region:** the app uses `AWS_REGION` (default `us-east-2`) for every service.
3. **S3 bucket:** create a bucket in that region and keep "Block all public access" **on**. Videos are shared through temporary presigned links, not public files. Set `S3_BUCKET` to its name.
4. **SNS SMS:** new accounts are in the SMS sandbox, so add and verify your phone number under *SNS → Text messaging (SMS) → Sandbox destination phone numbers*. Set `ALERT_PHONE_NUMBER` in E.164 format (e.g. `+15555550123`).
5. **Owner photo:** save a clear, front-facing photo of the owner as `referenceImage.jpg` in the project folder (or set `REFERENCE_IMAGE`). It is git-ignored so your face isn't committed.
6. **IAM permissions** the Pi's user needs (scope the S3 actions to your bucket):
   - `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`
   - `rekognition:CompareFaces`
   - `transcribe:StartTranscriptionJob`, `transcribe:GetTranscriptionJob`, `transcribe:DeleteTranscriptionJob`
   - `sns:Publish`

## Configuration

All settings live in `config.py`, and each one can be overridden with an environment variable of the same name. The ones you must set:

```bash
export S3_BUCKET="your-bucket-name"
```

```bash
export ALERT_PHONE_NUMBER="+15555550123"
```

```bash
export VOICE_PASSWORD="your secret phrase"
```

Other useful settings:

- `LATITUDE`, `LONGITUDE`, `TIMEZONE`: weather location
- `ALERT_COOLDOWN_SECONDS`: minimum time between alert SMS messages
- `POLL_INTERVAL_SECONDS`: how often the sensors are read
- `TEMP_HIGH_C`, `TEMP_LOW_C`, `HUMIDITY_HIGH`: indoor limits (the DHT11 reports Celsius)
- `FACE_SIMILARITY_THRESHOLD`, `VOICE_RECORD_SECONDS`: verification tuning

The optional `voice.jpg` and `camera.jpg` icons are used for the two verification buttons. Without them, plain text buttons are shown.

## Running

```bash
source .venv/bin/activate
```

```bash
python3 main.py
```

1. Click **Voice** and say your pass-phrase within the recording window. Transcription takes ~10–30 s.
2. Click **Camera** and look at the webcam.
3. When both pass, **Arm System** appears. Arming turns the laser on and starts polling the sensors every 5 seconds. Readings are printed to the terminal.
4. Each verification works for **one** arm or disarm, and expires after 2 minutes (`VERIFICATION_VALID_SECONDS`). To disarm, pass the voice and face checks again, then click **Disarm System**. This stops polling, turns the laser off and releases the GPIO pins. The window can't be closed while the system is armed.

The DHT11 often misses single readings ("Checksum did not validate"). The app retries automatically, and a missed reading never triggers an alarm on its own.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Tkinter GUI: verification flow, arm/disarm, clock, weather panel |
| `sensorDetection.py` | GPIO/DHT11 sensor reads, laser and LED control |
| `response.py` | Threat scoring, cost model, alarm video, alert message |
| `verification.py` | Webcam/microphone capture, S3 upload, Rekognition and Transcribe |
| `sendMessage.py` | SMS through AWS SNS |
| `weatherInformation.py` | Open-Meteo weather summary |
| `config.py` | All pins, thresholds and AWS/weather settings |
