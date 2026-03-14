# constant.py  --  Academix Comptable
# Themes clair/sombre + constantes de style
THEMES = {
    "clair": {
        "PRIMARY_BLUE":   "#0D47A1", "ACCENT_BLUE":    "#1565C0",
        "LIGHT_BLUE":     "#E8F0FE", "WHITE":          "#FFFFFF",
        "CARD_BG":        "#F5F7FA", "MAIN_BG":        "#EEF2FF",
        "TEXT_WHITE":     "#FFFFFF", "TEXT_DARK":      "#1E1E1E",
        "TEXT_GRAY":      "#666666", "TEXT_COLOR":     "#444444",
        "GRAY_BORDER":    "#DEE2E6", "SUCCESS_GREEN":  "#1B8B45",
        "LIGHT_GREEN":    "#E8F5E9", "WARNING_ORANGE": "#E67E22",
        "LIGHT_ORANGE":   "#FFF3E0", "DANGER_RED":     "#C0392B",
        "LIGHT_RED":      "#FFEBEE", "HEADER_BG":      "#0D47A1",
        "FOOTER_BG":      "#D8D8D8", "FOOTER_FG":      "#444444",
        "TREE_BG":        "#FFFFFF", "TREE_ODD":       "#F0F4FF",
        "SEP_COLOR":      "#DEE2E6", "SIDEBAR_BG":     "#0A3880",
    },
    "sombre": {
        "PRIMARY_BLUE":   "#1565C0", "ACCENT_BLUE":    "#1976D2",
        "LIGHT_BLUE":     "#1A2744", "WHITE":          "#1E2530",
        "CARD_BG":        "#252D3A", "MAIN_BG":        "#161B24",
        "TEXT_WHITE":     "#E8EAF6", "TEXT_DARK":      "#D0D8E8",
        "TEXT_GRAY":      "#8892A4", "TEXT_COLOR":     "#A0AABC",
        "GRAY_BORDER":    "#2E3A4A", "SUCCESS_GREEN":  "#2ECC71",
        "LIGHT_GREEN":    "#1A3027", "WARNING_ORANGE": "#F39C12",
        "LIGHT_ORANGE":   "#2E2010", "DANGER_RED":     "#E74C3C",
        "LIGHT_RED":      "#2E1010", "HEADER_BG":      "#0D1F3C",
        "FOOTER_BG":      "#0D1117", "FOOTER_FG":      "#8892A4",
        "TREE_BG":        "#1E2530", "TREE_ODD":       "#232C3A",
        "SEP_COLOR":      "#2E3A4A", "SIDEBAR_BG":     "#060E1C",
    }
}

_theme_actif = "clair"

def get_theme():     return THEMES[_theme_actif]
def is_dark():       return _theme_actif == "sombre"
def toggle_theme():
    global _theme_actif
    _theme_actif = "sombre" if _theme_actif == "clair" else "clair"
    _load(); return _theme_actif

def _load():
    g = globals()
    for k, v in get_theme().items():
        g[k] = v
_load()

FONT_TITLE     = ("Segoe UI", 16, "bold")
FONT_SUBTITLE  = ("Segoe UI", 13, "bold")
FONT_SECTION   = ("Segoe UI", 11, "bold")
TEXT_SECONDARY = ("Segoe UI", 10)
TEXT_SMALL     = ("Segoe UI",  9)
TEXT_BOLD      = ("Segoe UI", 10, "bold")
FONT_KPI       = ("Segoe UI", 17, "bold")
FONT_KPI_LBL   = ("Segoe UI",  9)
FONT_MONO      = ("Courier New", 10)

BTN_WIDTH      = 18
PAD_X          = 16
PAD_Y          = 10
ROW_HEIGHT     = 26
HEADER_H       = 70
FOOTER_H       = 36
LEFT_W         = 310
POLL_INTERVAL  = 8_000
ANNEE_SCOLAIRE = "2025-2026"