import logging

import shift_suite.config as config


def test_load_config_missing_file(tmp_path, monkeypatch, caplog):
    missing = tmp_path / "no.json"
    monkeypatch.setattr(config, "_CONFIG_PATH", missing)
    config._load_config.cache_clear()
    with caplog.at_level(logging.WARNING):
        assert config.get("x") is None
    assert "not found" in caplog.text


def test_load_config_invalid_json(tmp_path, monkeypatch, caplog):
    bad = tmp_path / "bad.json"
    bad.write_text("{ invalid", encoding="utf-8")
    monkeypatch.setattr(config, "_CONFIG_PATH", bad)
    config._load_config.cache_clear()
    with caplog.at_level(logging.ERROR):
        assert config.get("y", "d") == "d"
    assert "Failed to parse" in caplog.text


def test_reload_config(tmp_path, monkeypatch):
    cfg = tmp_path / "c.json"
    cfg.write_text('{"k": 1}', encoding="utf-8")
    monkeypatch.setattr(config, "_CONFIG_PATH", cfg)
    config.reload_config()
    assert config.get("k") == 1
    cfg.write_text('{"k": 2}', encoding="utf-8")
    config.reload_config()
    assert config.get("k") == 2
