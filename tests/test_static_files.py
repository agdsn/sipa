import pytest
from flask import Flask

from sipa.blueprints.documents import StaticFiles


@pytest.fixture(scope="module")
def documents_dir(tmp_path_factory: pytest.TempPathFactory):
    return tmp_path_factory.mktemp("documents")


@pytest.fixture(scope="module")
def static_file(documents_dir):
    path = documents_dir / "test.txt"
    with open(path, "w") as f:
        f.write("Test!")
    return path


@pytest.fixture(scope="module")
def app(static_file, documents_dir):
    app = Flask("test")
    app.add_url_rule(
        "/documents/<path:filename>",
        view_func=StaticFiles.as_view("show_document", documents_dir),
    )
    app.config.update(
        {
            "TESTING": True,
        }
    )
    return app


def test_static_view(app: Flask):
    with app.test_client() as c:
        resp = c.get("/documents/test.txt")
    assert resp.text == "Test!"
