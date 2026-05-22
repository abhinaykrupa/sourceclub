"""Detect supplier from file content or filename."""


def detect(file_bytes: bytes, filename: str) -> str:
    filename_lower = filename.lower()
    if "benco" in filename_lower:
        return "Benco"
    if "henry" in filename_lower or "schein" in filename_lower or "hs_" in filename_lower:
        return "Henry Schein"
    if "base86" in filename_lower or "b86" in filename_lower:
        return "Base86"
    if "darby" in filename_lower or "drb" in filename_lower:
        return "Darby"
    if "patterson" in filename_lower or "ptn" in filename_lower:
        return "Patterson"

    try:
        header = file_bytes[:2000].decode("utf-8", errors="ignore").lower()
        if "benco" in header:
            return "Benco"
        if "henry schein" in header:
            return "Henry Schein"
        if "base86" in header:
            return "Base86"
        if "darby" in header:
            return "Darby"
        if "patterson" in header:
            return "Patterson"
    except Exception:
        pass

    return "Unknown"
