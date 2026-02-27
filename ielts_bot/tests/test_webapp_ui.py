"""
Use-case tests for the IELTS webapp UI (app.js / main.css).

These tests parse JS and CSS source files to verify that the mobile-first
menu design meets readability and structure requirements without requiring
a running browser.

Use cases covered:
  UC-1: Menu screen has exactly 2 primary action buttons
  UC-2: Full Speaking (IELTS Speaking) button is the primary action
  UC-3: Parts button navigates to a parts sub-menu
  UC-4: Parts menu contains all 3 exam parts
  UC-5: Buttons meet minimum font-size for mobile readability
  UC-6: Buttons have minimum touch-target height (≥44 px)
  UC-7: Full Speaking button uses primary (brand) background color
  UC-8: Parts button uses secondary style
  UC-9: Stats button is present but visually de-emphasised
  UC-10: Back navigation from topic_selection respects prevScreen
"""

import os
import re
import sys
from pathlib import Path

import pytest

# ── Paths ──────────────────────────────────────────────────────────────────

WEBAPP_DIR = Path(__file__).parent.parent / "webapp"
APP_JS  = WEBAPP_DIR / "js" / "app.js"
CSS     = WEBAPP_DIR / "css" / "main.css"


def _js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _css() -> str:
    return CSS.read_text(encoding="utf-8")


# ── UC-1: Menu screen has 2 primary action buttons ─────────────────────────

class TestMenuStructure:
    def test_full_speaking_btn_exists(self):
        """UC-1/UC-2: full-speaking-btn must be in the menu screen HTML."""
        js = _js()
        assert 'id="full-speaking-btn"' in js

    def test_parts_btn_exists(self):
        """UC-1/UC-3: parts-btn must be in the menu screen HTML."""
        js = _js()
        assert 'id="parts-btn"' in js

    def test_stats_btn_exists(self):
        """UC-9: stats-btn must still be present in the menu."""
        js = _js()
        assert 'id="stats-btn"' in js

    def test_menu_does_not_render_part_cards_directly(self):
        """UC-1: part cards should only appear in parts_menu, not main menu."""
        js = _js()
        # Find the menu screen registration block (before parts_menu)
        menu_block_match = re.search(
            r'registerScreen\("menu".*?registerScreen\("parts_menu"',
            js, re.DOTALL
        )
        assert menu_block_match, "Could not find menu screen block"
        menu_block = menu_block_match.group(0)
        # part-card should NOT be in menu block directly
        assert 'class="part-card"' not in menu_block, (
            "part-card should be in parts_menu, not in main menu"
        )


# ── UC-3/UC-4: Parts menu screen structure ─────────────────────────────────

class TestPartsMenuScreen:
    def test_parts_menu_screen_registered(self):
        """UC-3: parts_menu screen must be registered."""
        js = _js()
        assert 'registerScreen("parts_menu"' in js

    def test_parts_menu_has_all_three_parts(self):
        """UC-4: parts_menu must render cards for parts 1, 2 and 3."""
        js = _js()
        # Find everything between registerScreen("parts_menu" and the next registerScreen
        parts_block_match = re.search(
            r'registerScreen\("parts_menu".*?(?=registerScreen\()',
            js, re.DOTALL
        )
        assert parts_block_match, "parts_menu screen block not found"
        block = parts_block_match.group(0)
        # Block should iterate over [1, 2, 3] and render data-part cards
        assert "[1, 2, 3]" in block or 'data-part' in block

    def test_parts_menu_wire_exists(self):
        """UC-3: WIRE must have a parts_menu handler."""
        js = _js()
        assert "parts_menu(" in js

    def test_parts_menu_wire_sets_prev_screen(self):
        """UC-10: Selecting a part from parts_menu must set prevScreen."""
        js = _js()
        # Find the parts_menu WIRE block
        wire_match = re.search(
            r'parts_menu\(el\)\s*\{(.*?)^\s*\},',
            js, re.DOTALL | re.MULTILINE
        )
        assert wire_match, "parts_menu WIRE block not found"
        wire_block = wire_match.group(1)
        assert "prevScreen" in wire_block, (
            "parts_menu WIRE must set state.prevScreen for correct back navigation"
        )


# ── UC-10: Back navigation uses prevScreen ──────────────────────────────────

class TestBackNavigation:
    def test_navigate_back_checks_prev_screen(self):
        """UC-10: navigateBack must use state.prevScreen for topic_selection."""
        js = _js()
        nav_match = re.search(
            r'async function navigateBack\(.*?\{(.*?)^\}',
            js, re.DOTALL | re.MULTILINE
        )
        assert nav_match, "navigateBack function not found"
        body = nav_match.group(1)
        assert "prevScreen" in body, (
            "navigateBack must read state.prevScreen to handle topic_selection correctly"
        )

    def test_topic_selection_wire_uses_prev_screen(self):
        """UC-10: topic_selection WIRE back button must use state.prevScreen."""
        js = _js()
        ts_match = re.search(
            r'topic_selection\(el\)\s*\{(.*?)^\s*\},',
            js, re.DOTALL | re.MULTILINE
        )
        assert ts_match, "topic_selection WIRE block not found"
        block = ts_match.group(1)
        assert "prevScreen" in block


# ── UC-5: Font sizes for mobile readability ─────────────────────────────────

class TestMobileFontSize:
    def _extract_rule(self, css: str, selector: str) -> str:
        """Extract the CSS block for a given selector (pass literal CSS selector, e.g. '.btn')."""
        pattern = re.escape(selector) + r'\s*\{([^}]*)\}'
        m = re.search(pattern, css)
        return m.group(1) if m else ""

    def _font_size_px(self, rule: str) -> float | None:
        m = re.search(r'font-size:\s*([\d.]+)px', rule)
        return float(m.group(1)) if m else None

    def test_btn_font_size_at_least_15px(self):
        """UC-5: .btn font-size must be ≥15px for legibility."""
        css = _css()
        rule = self._extract_rule(css, ".btn")
        size = self._font_size_px(rule)
        assert size is not None, ".btn must have an explicit font-size"
        assert size >= 15, f".btn font-size {size}px is below the 15px minimum"

    def test_full_speaking_btn_font_size_at_least_16px(self):
        """UC-5: .full-speaking-btn font-size must be ≥16px (primary CTA)."""
        css = _css()
        rule = self._extract_rule(css, ".full-speaking-btn")
        size = self._font_size_px(rule)
        assert size is not None, ".full-speaking-btn must have an explicit font-size"
        assert size >= 16, f".full-speaking-btn font-size {size}px is below 16px"


# ── UC-6: Minimum touch-target height ───────────────────────────────────────

class TestTouchTargetHeight:
    def _extract_rule(self, css: str, selector: str) -> str:
        pattern = re.escape(selector) + r'\s*\{([^}]*)\}'
        m = re.search(pattern, css)
        return m.group(1) if m else ""

    def _min_height_px(self, rule: str) -> float | None:
        m = re.search(r'min-height:\s*([\d.]+)px', rule)
        return float(m.group(1)) if m else None

    def test_btn_min_height_at_least_44px(self):
        """UC-6: .btn min-height must be ≥44px (Apple HIG touch target)."""
        css = _css()
        rule = self._extract_rule(css, ".btn")
        h = self._min_height_px(rule)
        assert h is not None, ".btn must have an explicit min-height"
        assert h >= 44, f".btn min-height {h}px is below the 44px minimum"

    def test_full_speaking_btn_min_height_at_least_56px(self):
        """UC-6: .full-speaking-btn should be taller as primary CTA (≥56px)."""
        css = _css()
        rule = self._extract_rule(css, ".full-speaking-btn")
        h = self._min_height_px(rule)
        assert h is not None, ".full-speaking-btn must have an explicit min-height"
        assert h >= 56, f".full-speaking-btn min-height {h}px is below 56px"

    def test_stats_btn_min_height_at_least_44px(self):
        """UC-6: .stats-btn must still be a tappable target (≥44px)."""
        css = _css()
        rule = self._extract_rule(css, ".stats-btn")
        h = self._min_height_px(rule)
        assert h is not None, ".stats-btn must have an explicit min-height"
        assert h >= 44, f".stats-btn min-height {h}px is below 44px"


# ── UC-7/UC-8: Button color semantics ───────────────────────────────────────

class TestButtonColorSemantics:
    def test_full_speaking_btn_uses_button_color(self):
        """UC-7: Full Speaking btn must use Telegram button-color (primary)."""
        css = _css()
        rule_match = re.search(
            r'\.full-speaking-btn\s*\{([^}]*)\}', css
        )
        assert rule_match, ".full-speaking-btn rule not found"
        rule = rule_match.group(1)
        assert "button-color" in rule, (
            ".full-speaking-btn background must reference --tg-theme-button-color"
        )

    def test_parts_btn_has_secondary_class_in_template(self):
        """UC-8: parts-btn must have btn-secondary class in the menu template."""
        js = _js()
        # Find the menu template and check parts-btn class
        assert 'btn-secondary' in js and 'parts-btn' in js, (
            "parts-btn should use btn-secondary class"
        )
        # Verify they appear near each other in the menu screen block
        menu_match = re.search(
            r'registerScreen\("menu".*?id="parts-btn"',
            js, re.DOTALL
        )
        assert menu_match, "parts-btn must be in menu screen"
        block = menu_match.group(0)
        assert "btn-secondary" in block
