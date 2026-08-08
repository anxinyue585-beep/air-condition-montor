from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.repository import DataRepository


def create_app(root: Path | None = None) -> FastAPI:
    app = FastAPI(
        title="城市空气质量查询服务",
        version="1.0.0",
        description="读取项目标准化数据、算法结果与 Open-Meteo 快照的只读 API。",
    )
    repository = DataRepository(root) if root else DataRepository()
    origins = [value.strip() for value in os.getenv("AQ_API_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if value.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict:
        return repository.health()

    @app.get("/api/overview")
    def overview() -> dict:
        return repository.overview()

    @app.get("/api/cities")
    def cities() -> dict:
        values = repository.cities()
        return {"items": values, "total": len(values)}

    @app.get("/api/lineage")
    def lineage() -> dict:
        return repository.lineage()

    @app.get("/api/processing/status")
    def processing_status() -> dict:
        return repository.processing_status()

    @app.get("/api/platform/hive/monthly")
    def hive_monthly(city: str = Query("", max_length=40), limit: int = Query(20, ge=1, le=200)) -> dict:
        return repository.hive_monthly(city, limit)

    @app.get("/api/records")
    def records(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        keyword: str = Query("", max_length=80),
        city: str = Query("", max_length=40),
        level: Literal["", "优", "良", "污染"] = "",
        quarter: Literal["", "Q1", "Q2", "Q3", "Q4"] = "",
        sort_key: Literal["id", "city", "date", "aqi", "level", "pm25", "pm10", "so2", "no2"] = "date",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> dict:
        return repository.records(
            page=page,
            page_size=page_size,
            keyword=keyword,
            city=city,
            level=level,
            quarter=quarter,
            sort_key=sort_key,
            sort_order=sort_order,
        )

    @app.get("/api/analysis/risk-ranking")
    def risk_ranking(limit: int = Query(10, ge=1, le=60)) -> dict:
        items = repository.risk_ranking(limit)
        return {"items": items, "total": len(items)}

    @app.get("/api/analysis/predictions")
    def predictions(
        model: Literal["ridge", "logistic"] = "ridge",
        city: str = Query("", max_length=40),
        limit: int = Query(20, ge=1, le=200),
    ) -> dict:
        items = repository.predictions(model, city, limit)
        return {"model": model, "items": items, "total": len(items)}

    @app.get("/api/analysis/spatial")
    def spatial_analysis() -> dict:
        try:
            return repository.spatial_analysis()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail="Spatial analysis result is not available") from exc

    @app.get("/api/analysis/pollution-warning")
    def pollution_warning(city: str = Query("", max_length=40)) -> dict:
        try:
            return repository.pollution_warning(city)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail="Pollution warning result is not available") from exc

    @app.get("/api/live/latest")
    def live_latest() -> dict:
        try:
            return repository.live_latest()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail="Open-Meteo latest snapshot is not available") from exc

    @app.get("/api/live/history")
    def live_history(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        city: str = Query("", max_length=40),
    ) -> dict:
        try:
            return repository.live_history(page, page_size, city)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail="Open-Meteo history is not available") from exc

    return app


app = create_app()
