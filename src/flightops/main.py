from fastapi import FastAPI


def create_app() -> FastAPI:
    application = FastAPI(
        title="FlightOps",
        version="0.1.0",
    )

    @application.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
