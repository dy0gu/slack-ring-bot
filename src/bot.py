import asyncio
import signal
from datetime import datetime
from pathlib import Path
from utils import env, EnvVar

from ring_doorbell import (
    AuthenticationError,
    Ring,
    RingDoorBell,
    Requires2FAError,
)

from ring_auth import RingAuthenticator
from slack_client import SlackNotifier

USER_AGENT = "slack-bot"
VIDEO_DIR = Path("videos")
POLL_INTERVAL_SECONDS = 2


class Bot:
    def __init__(self):
        ring_username = env(EnvVar.RING_USERNAME)
        ring_password = env(EnvVar.RING_PASSWORD)
        ring_otp = env(EnvVar.RING_OTP)
        slack_bot_token = env(EnvVar.SLACK_BOT_TOKEN)
        slack_channel_id = env(EnvVar.SLACK_CHANNEL_ID)

        self.authenticator = RingAuthenticator(
            ring_username, ring_password, USER_AGENT, ring_otp
        )
        self.slack = SlackNotifier(slack_bot_token, slack_channel_id)
        self.ring: Ring | None = None
        self.running = False
        self.recording_ids: dict[int, int] = {}

    async def handle_event(
        self,
        device: RingDoorBell,
        event_id: int,
        video_path: Path,
        device_name: str,
        timestamp: datetime,
    ) -> None:
        try:
            if not device.has_subscription:
                print(
                    f"\n❌ Device {device_name} does not have an active Ring subscription, cannot download video"
                )
                return

            print("\n📥 Downloading recording...")
            print(
                f"🔗 Recording URL: {await device.async_recording_url(event_id)}"
            )

            await device.async_recording_download(
                event_id,
                filename=str(video_path),
                override=True,
            )

            if not video_path.exists():
                print(f"❌ Failed to download video to {video_path}")
                return
            else:
                print(f"✅ Video downloaded to {video_path}")

            await self.slack.send_video(
                video_path=video_path,
                device_name=device_name,
                timestamp=timestamp,
            )
        except Exception as e:
            print(f"❌ Error downloading/sending video: {e}")

    async def poll(self) -> None:
        assert self.ring is not None
        await self.ring.async_update_data()
        devices = self.ring.devices()

        for device in devices.video_devices:
            try:
                latest_id = await device.async_get_last_recording_id()

                if latest_id:
                    previous_id = self.recording_ids.get(device.id)

                    if previous_id is None:
                        self.recording_ids[device.id] = latest_id

                    elif latest_id != previous_id:
                        print(f"🔔 New event detected on {device.name}")

                        self.recording_ids[device.id] = latest_id

                        timestamp = datetime.now()
                        filename = f"{device.id}_latest.mp4"
                        video_path = VIDEO_DIR / filename

                        # Download and send video
                        await self.handle_event(
                            device=device,
                            event_id=latest_id,
                            video_path=video_path,
                            device_name=device.name,
                            timestamp=timestamp,
                        )

            except Exception as e:
                if not self.running:
                    return
                print(f"❌ Error polling device {device.name}: {e}")

    async def start(self) -> None:
        print("🚀 Starting...")
        try:
            print("🚪 Logging in with Ring credentials...")
            auth = await self.authenticator.async_authenticate()
            self.ring = Ring(auth)
            await self.ring.async_create_session()
            await self.ring.async_update_data()
            print("✅ Ring session created")
        except Requires2FAError:
            print(
                "🔒 Authentication error: Account is rate-limited, wait an hour before trying again"
            )
            await self.stop()
            return
        except AuthenticationError as e:
            print(f"🔒 Authentication error: {e}")
            await self.stop()
            return
        try:
            assert self.ring is not None
            devices = self.ring.devices()
            if devices.video_devices.count == 0:
                print("❌ No video devices found in Ring account.")
                await self.stop()
                return
            print("\n📷 Connected video devices:")
            for video_device in devices.video_devices:
                print(f"\n\t🟢 {video_device.name} (ID: {video_device.id})")

            VIDEO_DIR.mkdir(exist_ok=True)

            print(
                f"\n👂 Polling for new video events every {POLL_INTERVAL_SECONDS} seconds...\n"
            )

            self.running = True

            while self.running:
                await self.poll()
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except Exception as e:
            if not self.running:
                return
            print(f"❌ Unexpected error: {e}")
            await self.stop()
            return

    async def stop(self) -> None:
        print("\n🛑 Stopping bot...")
        self.running = False

        if self.authenticator:
            print("🔒 Closing authentication session...")
            await self.authenticator.async_close()

        print("✅ Bot stopped gracefully")


async def main() -> None:
    bot = Bot()

    # Handle shutdown signals
    # ==========================
    loop = asyncio.get_running_loop()

    def signal_handler() -> None:
        print("\n❗Shutdown signal received...")
        loop.create_task(bot.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    # ==========================

    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
