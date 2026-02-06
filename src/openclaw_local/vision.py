from __future__ import annotations

import ctypes.util
import importlib
import sys
from dataclasses import dataclass
from typing import Generator


@dataclass(frozen=True)
class VisionSupport:
    cv2_available: bool
    mediapipe_available: bool

    @property
    def ok(self) -> bool:
        return self.cv2_available and self.mediapipe_available


class VisionService:
    def support(self) -> VisionSupport:
        cv2_available = importlib.util.find_spec("cv2") is not None
        mediapipe_available = importlib.util.find_spec("mediapipe") is not None

        if sys.platform.startswith("linux") and ctypes.util.find_library("GL") is None:
            cv2_available = False

        return VisionSupport(
            cv2_available=cv2_available,
            mediapipe_available=mediapipe_available,
        )

    def stream_mjpeg(self) -> Generator[bytes, None, None]:
        cv2 = importlib.import_module("cv2")
        mediapipe = importlib.import_module("mediapipe")

        mp_hands = mediapipe.solutions.hands
        mp_draw = mediapipe.solutions.drawing_utils

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            message = b"Camera unavailable"
            frame = (
                b"--frame\r\n"
                b"Content-Type: text/plain\r\n\r\n" + message + b"\r\n"
            )
            yield frame
            return

        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as hands:
            while True:
                success, frame = cap.read()
                if not success:
                    break

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(
                            frame,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                        )

                ok, buffer = cv2.imencode(".jpg", frame)
                if not ok:
                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
                )

        cap.release()
