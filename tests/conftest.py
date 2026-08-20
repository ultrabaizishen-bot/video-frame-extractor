"""pytest 公共 fixture。"""
import os
import pytest

# 测试视频路径（项目根目录下的刑具.mp4）
VIDEO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "刑具.mp4",
)


@pytest.fixture
def video_path() -> str:
    return VIDEO_PATH
