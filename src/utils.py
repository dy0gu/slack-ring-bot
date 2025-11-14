from enum import Enum
import os
import sys

from dotenv import load_dotenv

load_dotenv()


class EnvVar(Enum):
    RING_USERNAME = "RING_USERNAME"
    RING_PASSWORD = "RING_PASSWORD"
    RING_OTP = "RING_OTP"
    SLACK_BOT_TOKEN = "SLACK_BOT_TOKEN"
    SLACK_CHANNEL_ID = "SLACK_CHANNEL_ID"


def env(key: EnvVar) -> str:
    value = os.getenv(key.value)
    if not value:
        print(f"Error: Missing required environment variable: {key.value}")
        sys.exit(1)
    return value
