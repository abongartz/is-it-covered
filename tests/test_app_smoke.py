from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def test_home_page_renders_without_error():
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.title[0].value == "Is it covered?"


def test_home_page_lists_the_corpus():
    app = AppTest.from_file(str(APP)).run()
    assert any("Ethias" in h.value for h in app.subheader)
    assert any("chapitres" in m.value for m in app.markdown)
