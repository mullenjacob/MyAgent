from openclaw_local.vision import VisionService


def test_vision_support_false(monkeypatch) -> None:
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    support = VisionService().support()
    assert support.ok is False
    assert support.cv2_available is False
    assert support.mediapipe_available is False


def test_vision_support_true(monkeypatch) -> None:
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
    monkeypatch.setattr("ctypes.util.find_library", lambda name: "libGL.so.1")
    support = VisionService().support()
    assert support.ok is True
