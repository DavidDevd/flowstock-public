from __future__ import annotations

import uvicorn


def run() -> None:
    uvicorn.run(
        "flowstock_api.main:app",
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
    )


if __name__ == "__main__":
    run()
