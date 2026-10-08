"""Embed the dashboard source in firmware; run after editing the HTML."""
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "vendor/MeshCore/examples/companion_radio"
page = (root / "RepeaterMonitorPage.html").read_text(encoding="utf-8")
assert ')MONITORHTML"' not in page
# Catch Windows-1252 mojibake before embedding the dashboard.
assert not any(marker in page for marker in ("\u00c2", "\u00c3", "\u00e2\u20ac", "\u00f0\u0178", "\ufffd")), "Dashboard contains corrupted UTF-8 characters"
(root / "RepeaterMonitorPage.h").write_text(
    '#pragma once\n// Generated from RepeaterMonitorPage.html by scripts/build-monitor-page.py\n'
    'static const char MONITOR_PAGE[] PROGMEM = R"MONITORHTML(' + page + ')MONITORHTML";\n',
    encoding="utf-8",
)
