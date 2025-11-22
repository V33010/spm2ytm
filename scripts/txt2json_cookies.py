import json


def cookies_txt_to_json(txt_path, json_path):
    cookies = []
    with open(txt_path, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue

            parts = line.strip().split("\t")
            if len(parts) != 7:
                continue

            domain, flag, path, secure, expiry, name, value = parts

            cookies.append(
                {
                    "domain": domain,
                    "path": path,
                    "secure": secure.lower() == "true",
                    "name": name,
                    "value": value,
                    "expires": int(expiry) if expiry != "0" else None,
                    "httpOnly": False,
                    "sameSite": "Lax",
                }
            )

    with open(json_path, "w") as f:
        json.dump(cookies, f, indent=2)


cookies_txt_to_json("cookies.txt", "cookies.json")
