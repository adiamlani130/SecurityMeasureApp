"""Central configuration for SecurityMeasureApp.

Every value can be overridden with an environment variable of the same name,
so you can keep secrets/personal values out of the code, e.g.:

    export ALERT_PHONE_NUMBER="+15555550123"
    export S3_BUCKET="my-security-bucket"
    python3 main.py
"""
import os


def _env(name, default):
    return os.environ.get(name, default)


def _env_int(name, default):
    value = os.environ.get(name)
    return int(value) if value not in (None, "") else default


def _env_float(name, default):
    value = os.environ.get(name)
    return float(value) if value not in (None, "") else default


def _env_bool(name, default):
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# AWS
# ---------------------------------------------------------------------------
# Credentials come from the normal AWS chain (~/.aws/credentials, `aws configure`,
# or AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars). Never hardcode keys here.
AWS_REGION = _env("AWS_REGION", "us-east-2")

# One private bucket is used for the voice password recordings and the alarm videos.
S3_BUCKET = _env("S3_BUCKET", "")

# How long the link to an alarm video (sent by SMS) stays valid. 7 days is the AWS max.
VIDEO_LINK_EXPIRY_SECONDS = _env_int("VIDEO_LINK_EXPIRY_SECONDS", 7 * 24 * 3600)

# Phone number that receives alerts, in E.164 format (e.g. +15555550123).
# In the SNS sandbox this number must be verified in the SNS console first.
ALERT_PHONE_NUMBER = _env("ALERT_PHONE_NUMBER", "")

# ---------------------------------------------------------------------------
# Identity verification
# ---------------------------------------------------------------------------
# Photo of the owner's face that captured pictures are compared against.
REFERENCE_IMAGE = _env("REFERENCE_IMAGE", "referenceImage.jpg")
# Minimum Rekognition similarity (0-100) to count as a match.
FACE_SIMILARITY_THRESHOLD = _env_float("FACE_SIMILARITY_THRESHOLD", 90)

# Spoken pass-phrase. Matching is case-insensitive and ignores punctuation.
VOICE_PASSWORD = _env("VOICE_PASSWORD", "open sesame")
VOICE_RECORD_SECONDS = _env_int("VOICE_RECORD_SECONDS", 5)
# ALSA device passed to `arecord -D` (run `arecord -l` to list). Empty = system default.
AUDIO_DEVICE = _env("AUDIO_DEVICE", "")
# Give up on an AWS Transcribe job after this many seconds.
TRANSCRIBE_TIMEOUT_SECONDS = _env_int("TRANSCRIBE_TIMEOUT_SECONDS", 180)

# Index of the webcam for OpenCV (0 = first camera).
CAMERA_INDEX = _env_int("CAMERA_INDEX", 0)

# ---------------------------------------------------------------------------
# GPIO pins (BCM numbering, i.e. the "GPIO17" style numbers, not physical pin numbers)
# ---------------------------------------------------------------------------
GAS_PIN = _env_int("GAS_PIN", 17)        # MQ-2 digital out (DO)
FLAME_PIN = _env_int("FLAME_PIN", 27)    # Flame sensor digital out (DO)
DHT_PIN = _env_int("DHT_PIN", 4)         # DHT11 data
MOTION_PIN = _env_int("MOTION_PIN", 22)  # HC-SR501 PIR out
RAIN_PIN = _env_int("RAIN_PIN", 23)      # Rain sensor digital out (DO)
LASER_PIN = _env_int("LASER_PIN", 24)    # KY-008 laser signal (armed indicator)

# Most MQ-2 / flame / rain breakout boards pull DO *low* when they detect something,
# while the HC-SR501 drives its output *high*. Flip these if your modules differ.
GAS_ACTIVE_LOW = _env_bool("GAS_ACTIVE_LOW", True)
FLAME_ACTIVE_LOW = _env_bool("FLAME_ACTIVE_LOW", True)
RAIN_ACTIVE_LOW = _env_bool("RAIN_ACTIVE_LOW", True)
MOTION_ACTIVE_LOW = _env_bool("MOTION_ACTIVE_LOW", False)

# Optional status LEDs, one per sensor. Set a pin to light that LED while the
# sensor is triggered; leave at -1 to disable.
GAS_LED_PIN = _env_int("GAS_LED_PIN", -1)
FLAME_LED_PIN = _env_int("FLAME_LED_PIN", -1)
MOTION_LED_PIN = _env_int("MOTION_LED_PIN", -1)
RAIN_LED_PIN = _env_int("RAIN_LED_PIN", -1)

# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------
POLL_INTERVAL_SECONDS = _env_float("POLL_INTERVAL_SECONDS", 5)
# Minimum time between two alerts (each alert records video and sends an SMS).
ALERT_COOLDOWN_SECONDS = _env_float("ALERT_COOLDOWN_SECONDS", 120)
ALARM_VIDEO_SECONDS = _env_int("ALARM_VIDEO_SECONDS", 5)

# Indoor temperature/humidity limits (the DHT11 reports Celsius).
TEMP_HIGH_C = _env_float("TEMP_HIGH_C", 32)  # ~90 °F
TEMP_LOW_C = _env_float("TEMP_LOW_C", 4)     # ~40 °F
HUMIDITY_HIGH = _env_float("HUMIDITY_HIGH", 70)

# ---------------------------------------------------------------------------
# Weather (Open-Meteo, no API key needed)
# ---------------------------------------------------------------------------
LATITUDE = _env_float("LATITUDE", 39.29)     # Baltimore, MD - change to your location
LONGITUDE = _env_float("LONGITUDE", -76.61)
TIMEZONE = _env("TIMEZONE", "America/New_York")
