from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    url: str = Field(
        ...,
        min_length=1,
        max_length=2048
    )


class GenerateProjectRequest(BaseModel):
    app_name: str = Field(
        default="My Web App",
        min_length=1,
        max_length=100
    )

    package_name: str = Field(
        default="com.example.myapp",
        min_length=3,
        max_length=200
    )

    start_url: str = Field(
        ...,
        min_length=1,
        max_length=2048
    )

    version_name: str = Field(
        default="1.0.0",
        min_length=1,
        max_length=30
    )

    fullscreen: bool = True
    offline_cache: bool = True
    push_notifications: bool = False
    native_bridge: bool = False

    min_sdk: int = Field(
        default=23,
        ge=21,
        le=35
    )

    target_sdk: int = Field(
        default=35,
        ge=28,
        le=35
    )

    orientation: str = "portrait"