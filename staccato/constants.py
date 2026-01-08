"""Constants for Staccato application."""


CANONICAL_KEY_ORDER = {
    "esc": 0,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "0": 10, "-": 11, "=": 12, "backspace": 13,
    "tab": 20, "q": 21, "w": 22, "e": 23, "r": 24, "t": 25, "y": 26, "u": 27, "i": 28, "o": 29, "p": 30, "[": 31, "]": 32, "\\": 33,
    "left ctrl": 40, "a": 41, "s": 42, "d": 43, "f": 44, "g": 45, "h": 46, "j": 47, "k": 48, "l": 49, ";": 50, "'": 51, "enter": 52,
    "left shift": 60, "z": 61, "x": 62, "c": 63, "v": 64, "b": 65, "n": 66, "m": 67, ",": 68, ".": 69, "/": 70,
    "left alt": 80, "space": 81, "right alt": 82,
    "f1": 100, "f2": 101, "f3": 102, "f4": 103, "f5": 104, "f6": 105, "f7": 106, "f8": 107, "f9": 108, "f10": 109, "f11": 110, "f12": 111
}

VIEW_WINDOW_SECONDS = 5.0

VIEW_RESOLUTION = 0.05

TIMELINE_BLOCK_WIDTH = 100

# Finger Adhesion Severity Thresholds (milliseconds)
ADHESION_THRESHOLD_MINOR = 50      # Existing threshold - yellow warning
ADHESION_THRESHOLD_MODERATE = 100  # Orange alert
ADHESION_THRESHOLD_SEVERE = 150    # Red critical

# Severity Colors (Tokyo Night palette)
SEVERITY_COLOR_CLEAN = "#9ece6a"     # Green
SEVERITY_COLOR_MINOR = "#e0af68"     # Yellow/Orange
SEVERITY_COLOR_MODERATE = "#ff9e64"  # Orange
SEVERITY_COLOR_SEVERE = "#f7768e"    # Red

# Signal Hygiene Score Weights
HYGIENE_WEIGHT_CLEAN = 1.0
HYGIENE_WEIGHT_MINOR = 0.7
HYGIENE_WEIGHT_MODERATE = 0.3
HYGIENE_WEIGHT_SEVERE = 0.0
