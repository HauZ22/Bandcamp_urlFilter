import streamlit as st


def run_inline_script(script: str, *, height: int = 0) -> None:
    body = str(script or "").strip()
    if not body:
        return
    if "<script" not in body.lower():
        body = f"<script>{body}</script>"

    normalized_height = max(0, int(height))
    iframe_api = getattr(st, "iframe", None)
    if callable(iframe_api):
        iframe_api(body, height=normalized_height)
        return

    from streamlit.components.v1 import html as component_html

    component_html(body, height=normalized_height, width=0)
