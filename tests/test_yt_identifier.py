import pytest

from ai_xp.transcript import extract_video_id


@pytest.mark.parametrize(
    "url, expected",
    [
        # Formats standard
        ("https://www.youtube.com/watch?v=abc123", "abc123"),
        ("http://youtube.com/watch?v=def456", "def456"),
        ("https://youtube.com/watch?v=ghi789&feature=shared", "ghi789"),
        ("https://m.youtube.com/watch?v=jkl012&t=10s", "jkl012"),
        # Format raccourci youtu.be
        ("https://youtu.be/mno345", "mno345"),
        ("http://youtu.be/pqr678?t=10", "pqr678"),
        ("https://youtu.be/stu901&feature=shared", "stu901"),
        # Shorts
        ("https://www.youtube.com/shorts/vwx234", "vwx234"),
        ("https://youtube.com/shorts/yzab56?feature=shared", "yzab56"),
        ("https://m.youtube.com/shorts/cdef78", "cdef78"),
        # Cas spéciaux
        ("https://youtube.com/embed/ghj789", "ghj789"),  # Format embed
        ("https://vimeo.com/123456", None),  # Pas YouTube
        ("https://example.com?url=fake", None),  # Pas YouTube
        ("", None),  # Chaîne vide
    ],
)
def test_get_video_id(url: str, expected: str | None):
    assert extract_video_id(url) == expected
