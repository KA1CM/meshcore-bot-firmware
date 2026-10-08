# Battery voltage signature experiment

Admin dashboard: expand **Battery voltage signature test**. Use Wi-Fi while the bot runs from its wall charger and installed 18650.

1. Start test with USB connected; wait about 120 seconds.
2. Unplug USB and immediately click **Mark Unplugged**; wait about 120 seconds.
3. Reconnect USB and immediately click **Mark Restored**; wait about 120 seconds.
4. Stop, then Download CSV. Save before rebooting or starting another test.

Sampling continues with the browser closed or Wi-Fi disconnected. Up to 601 samples / ten minutes are kept in RAM (about 4.8 KB, allocated only on first start); Clear releases the buffer. No flash writes or USB serial debug output. The existing board ADC routine takes about 10 ms per sample. Main-loop stalls can delay samples: actual elapsed milliseconds are recorded, with no fabricated catch-up samples. CSV download requires the test to be stopped and is streamed in small chunks.

CSV includes start UTC (0 if NTP unavailable), manual unplug/restore marker times, elapsed milliseconds, battery millivolts, manual phase, and internet lookup activity at sampling time. Markers represent dashboard clicks, not measured USB transitions. Unmarked events have timestamp 0. ADC readings are quantized and radio/load transients may appear; continuous voltage-signature monitoring now runs independently and sends admin DMs on confirmed power changes. Manual CSV markers do not affect those alerts.

Compare the final 30–60 seconds before each marker against readings around 1, 5, 10, 30, 60 and 120 seconds afterward. Repeat at different battery charge levels and during ordinary radio traffic before selecting thresholds. A voltage signature may be too weak or inconsistent for reliable detection.

Host regression: `tests/firmware_bot/test_battery_signature.py`. Firmware build and physical measurements remain manual.

Continuous monitoring: UsbPowerDetector.h; calibration assumes USB connected at startup. All three captured CSVs replay with exactly one lost/restored event each.
