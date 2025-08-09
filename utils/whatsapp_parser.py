def parse_inbound(data: dict):
    content = (data.get("message") or {}).get("content") or {}
    text = None
    choice = None
    payload_type = "unknown"

    if data.get("message_type") == "reply":
        rep = data.get("reply") or {}
        choice = rep.get("id") or rep.get("title")
        payload_type = "reply"

    if not text and content.get("type") == "text":
        text = content.get("text")
        payload_type = "text"

    if not choice and content.get("type") == "button":
        btn = content.get("button", {}) or {}
        choice = btn.get("payload") or btn.get("text")
        payload_type = "button"

    if not choice:
        custom = content.get("custom") or {}
        interactive = custom.get("interactive") or {}
        btn_reply = interactive.get("button_reply") or {}
        if btn_reply:
            choice = btn_reply.get("id") or btn_reply.get("title")
            payload_type = "button"

    if not text:
        text = content.get("text") or data.get("text")

    sender = (data.get("from") or {})
    if isinstance(sender, dict):
        user_number = sender.get("number") or sender.get("id")
    else:
        user_number = str(sender) if sender else None

    return {
        "user_number": user_number,
        "text": text,
        "choice": choice,
        "payload_type": payload_type,
    }
