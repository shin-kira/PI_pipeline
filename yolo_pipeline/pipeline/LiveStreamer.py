import asyncio
import cv2
import threading
from livekit import rtc
from livekit.api import AccessToken, VideoGrants

livestram_url = "wss://boat-a492rp4j.livekit.cloud"
livestream_API = "API6vgBQqDcvLza"
livestram_secret = "ZrAlSabuuCjetsvbDBv7eIthxwUmkCZE3MTx6B0YQiL"
Identity = "boat-control-system-PI4"

_streaming_loop = None
_streaming_room = None
_streaming_video_source = None


def generate_token(boatname: str, boatId: int):
    token = (
        AccessToken(livestream_API, livestram_secret)
        .with_identity(Identity)
        .with_name("PI4")
        .with_grants(
            VideoGrants(
                room_join=True,
                room=f"{boatname}:{boatId}",
                can_publish=True,
                can_subscribe=False,
            )
        )
    )
    return token.to_jwt()


async def _connect_and_stream(boatname: str, boatId: int):
    global _streaming_room, _streaming_video_source
    token = generate_token(boatname, boatId)
    room = rtc.Room()
    print(f"Connecting to LiveKit room: {boatname}:{boatId}...", flush=True)
    await room.connect(livestram_url, token)
    print("Connected successfully!", flush=True)

    video_source = rtc.VideoSource(640, 480)
    track = rtc.LocalVideoTrack.create_video_track("yolo-stream", video_source)
    options = rtc.TrackPublishOptions()
    options.source = rtc.TrackSource.SOURCE_CAMERA
    await room.local_participant.publish_track(track, options)
    print("Video track published. Streaming live...", flush=True)

    _streaming_room = room
    _streaming_video_source = video_source

    while True:
        await asyncio.sleep(0.1)


def start_streaming(boatname: str, boatId: int):
    def run_loop():
        global _streaming_loop
        _streaming_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_streaming_loop)
        try:
            _streaming_loop.run_until_complete(_connect_and_stream(boatname, boatId))
        except Exception as e:
            print(f"Streaming error: {e}", flush=True)

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    return t


def push_frame(frame_bgr):
    global _streaming_video_source, _streaming_loop
    if _streaming_video_source is None or _streaming_loop is None:
        return False

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    height, width, _ = frame_rgb.shape
    frame_to_push = rtc.VideoFrame(
        width, height, rtc.VideoBufferType.RGB24, frame_rgb.tobytes()
    )

    try:
        coro = _streaming_video_source.capture_frame(frame_to_push)
        if asyncio.iscoroutine(coro):
            fut = asyncio.run_coroutine_threadsafe(coro, _streaming_loop)
            fut.result(timeout=0.1)
        return True
    except Exception as e:
        print(f"Push frame error: {e}", flush=True)
        return False