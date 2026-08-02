import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from nutrichat.app.ui import CUSTOM_CSS, CUSTOM_HEAD, build_demo


RESEARCH_ASSETS_DIR = Path(__file__).resolve().parent / "research_assets"

demo = build_demo()

if __name__ == "__main__":
    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    demo.queue().launch(
        server_name=server_name,
        server_port=server_port,
        theme=gr.themes.Default(),
        css=CUSTOM_CSS,
        head=CUSTOM_HEAD,
        allowed_paths=[RESEARCH_ASSETS_DIR],
    )
