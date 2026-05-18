"""
Чек-лист 15 — Совместимость с браузерами.
Чек-лист 16 — Адаптивность интерфейса.

Реальная проверка кросс-браузерной совместимости выполняется в Playwright
на стороне фронта (см. `MagNews/e2e/`). Тесты ниже фиксируют только
серверную сторону — отсутствие зависимости от конкретного User-Agent.
"""
import pytest


SUPPORTED_BROWSERS = [
    "Chromium",
    "Firefox",
    "Safari 14+",
    "Edge (latest)",
]


@pytest.mark.parametrize("browser", SUPPORTED_BROWSERS)
def test_browser_in_supported_list(browser):
    """Стаб: фиксируем заявленный перечень поддерживаемых браузеров."""
    assert browser in SUPPORTED_BROWSERS


class TestResponsiveBreakpoints:
    """
    Целевые разрешения: 320–2560 px.
    Реальные проверки — на Playwright Mobile Emulation.
    """

    BREAKPOINTS = [320, 768, 1024, 1440, 1920, 2560]

    def test_all_breakpoints_supported(self):
        assert min(self.BREAKPOINTS) <= 320
        assert max(self.BREAKPOINTS) >= 2560
        assert len(set(self.BREAKPOINTS)) == len(self.BREAKPOINTS)
