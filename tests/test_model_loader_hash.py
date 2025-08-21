from symphonia.runtime.model_loader import ModelLoader


def test_bundle_hash_ignores_hidden(tmp_path):
    loader = ModelLoader(cache_dir=tmp_path / "c")
    d = tmp_path / "bundle"
    d.mkdir()
    (d / "a.txt").write_text("a")
    (d / ".DS_Store").write_text("x")
    h1 = loader._bundle_hash(d)

    # Changing ignored files doesn't affect the hash
    (d / ".DS_Store").write_text("y")
    (d / "b.tmp").write_text("tmp")
    h2 = loader._bundle_hash(d)
    assert h1 == h2

    # Modifying a real file changes the hash
    (d / "a.txt").write_text("b")
    h3 = loader._bundle_hash(d)
    assert h3 != h1

