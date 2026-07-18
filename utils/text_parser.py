"""Shared text parsing utilities."""

import re


def parse_lines(text):
    """Split text into non-empty stripped lines.

    This pattern was duplicated 4+ times in the original code.
    """
    return [line.strip() for line in text.strip().split("\n") if line.strip()]


def parse_customer_info(text):
    """Extract customer name, national code, and phone from free-form text.

    Supports both single-line (mixed) and multi-line input formats.
    """
    info = {"name": "", "national_code": "", "phone": ""}
    national_code_pattern = r'\b\d{10}\b'
    phone_pattern = r'\b09\d{9}\b'
    lines = parse_lines(text)

    if not lines:
        return info

    if len(lines) == 1:
        line = lines[0]
        nc_match = re.search(national_code_pattern, line)
        if nc_match:
            info["national_code"] = nc_match.group()
            line = line.replace(nc_match.group(), "")
        phone_match = re.search(phone_pattern, line)
        if phone_match:
            info["phone"] = phone_match.group()
            line = line.replace(phone_match.group(), "")
        info["name"] = line.strip().replace(",", " ").replace("-", " ")
    else:
        info["name"] = lines[0]
        if len(lines) >= 2:
            if re.match(national_code_pattern, lines[1]):
                info["national_code"] = lines[1]
            elif re.match(phone_pattern, lines[1]):
                info["phone"] = lines[1]
            else:
                info["national_code"] = lines[1]
        if len(lines) >= 3:
            if re.match(phone_pattern, lines[2]):
                info["phone"] = lines[2]
            elif re.match(national_code_pattern, lines[2]):
                info["national_code"] = lines[2]
            else:
                info["phone"] = lines[2]

    info["name"] = info["name"].strip()
    return info
