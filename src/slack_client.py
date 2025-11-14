"""Slack client helper module."""

from datetime import datetime
from pathlib import Path

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackNotifier:
    def __init__(self, token: str, channel_id: str):
        self.client = WebClient(token=token)
        self.channel_id = channel_id

    async def send_video(
        self,
        video_path: str | Path,
        device_name: str,
        event_type: str,
        timestamp: datetime,
        message: str | None = None,
    ) -> bool:
        video_path = Path(video_path)

        if not video_path.exists():
            print(f"❌ Video file not found: {video_path}")
            return False

        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        title = f"🔔 {device_name} - {event_type.capitalize()}"
        initial_comment = f"{title}\n📅 {time_str}"
        if message:
            initial_comment += f"\n{message}"

        try:
            print(f"💬 Uploading video to Slack channel {self.channel_id}...")
            response = self.client.files_upload_v2(
                channel=self.channel_id,
                file=str(video_path),
                title=title,
                initial_comment=initial_comment,
            )

            if response["ok"]:
                print("✅ Video uploaded successfully to Slack")
                video_path.unlink()
                print(f"🗑️ Cleaned up local video file: {video_path}")
                return True
            else:
                print(f"❌ Failed to upload video: {response}")
                return False

        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            print(f"❌ Error uploading video to Slack: {e}")
            return False

    async def send_message(
        self, text: str, channel_id: str | None = None
    ) -> bool:
        target_channel = channel_id or self.channel_id

        try:
            response = self.client.chat_postMessage(
                channel=target_channel,
                text=text,
            )
            return bool(response.get("ok", False))
        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            print(f"❌ Error sending message to Slack: {e}")
            return False
