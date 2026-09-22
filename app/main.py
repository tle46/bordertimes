from datetime import datetime
import json
from pathlib import Path
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import app.services.cbp_service as cbp_service
import app.services.cbsa_service as cbsa_service
import app.services.observation_service as observation_service


app = FastAPI(
    title="US-Canada Border API",
    description="API for US-Canada border crossing observations.",
    version="1.0.0",
)

origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# bordermapping.json is located in the project root.
# This file is assumed to be at: project_root/app/main.py
MAPPING_FILE = Path(__file__).parent.parent / "bordermapping.json"


def load_border_mapping():
    """Load border crossing metadata from bordermapping.json."""
    try:
        with MAPPING_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        raise RuntimeError(
            f"Border mapping file not found: {MAPPING_FILE}"
        )

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in border mapping file: {exc}"
        )


def get_observations():
    """Fetch and combine CBP and CBSA data."""
    cbp = cbp_service.CBPService()
    cbplist = cbp.get_cbp()

    cbsa = cbsa_service.CBSAService()
    cbsalist = cbsa.get_cbsa()

    return observation_service.build_observations(
        cbp_list=cbplist,
        cbsa_list=cbsalist,
        mapping_file=str(MAPPING_FILE),
        observation_time=datetime.now().astimezone(),
    )

def get_combined_borders():
    """Fetch live observations and combine them with border metadata."""
    observations = get_observations()
    mapping = load_border_mapping()

    observations_by_id = {
        str(observation.border_id): observation
        for observation in observations
    }

    combined = []

    for border in mapping:
        border_id = str(border["border_id"])
        observation = observations_by_id.get(border_id)

        if observation:
            observation_data = {
                "uscan_passenger_lanes": observation.uscan_passenger_lanes,
                "uscan_passenger_delay": observation.uscan_passenger_delay,
                "uscan_commercial_lanes": observation.uscan_commercial_lanes,
                "uscan_commercial_delay": observation.uscan_commercial_delay,
                "uscan_updated": observation.uscan_updated,
                "canus_passenger_lanes": observation.canus_passenger_lanes,
                "canus_passenger_delay": observation.canus_passenger_delay,
                "canus_commercial_lanes": observation.canus_commercial_lanes,
                "canus_commercial_delay": observation.canus_commercial_delay,
                "canus_updated": observation.canus_updated,
                "observation_time": observation.observation_time,
            }
        else:
            observation_data = None

        combined.append({
            **border,
            "delay": observation_data,
        })

    return combined



@app.get("/")
def root():
    return {
        "name": "US-Canada Border Wait Time API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.get("/borders")
def mapping():
    """Return all border crossing mappings."""
    try:
        data = load_border_mapping()

        return {
            "count": len(data),
            "borders": data,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load border mapping: {exc}",
        )


@app.get("/borders/{border_id}")
def mapping_by_id(border_id: int):
    """Return mapping information for a specific border."""
    try:
        data = load_border_mapping()

        for border in data:
            if border["border_id"] == border_id:
                return border

        raise HTTPException(
            status_code=404,
            detail=f"Border mapping '{border_id}' not found",
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load border mapping: {exc}",
        )


@app.get("/delays/{border_id}")
def observation(border_id: str):
    try:
        data = get_observations()

        for item in data:
            if str(item.border_id) == border_id:
                return item

        raise HTTPException(
            status_code=404,
            detail=f"Border crossing '{border_id}' not found",
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve observation: {exc}",
        )


@app.get("/delays")
def borders():
    try:
        data = get_observations()

        return {
            "count": len(data),
            "borders": data,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve borders: {exc}",
        )

@app.get("/borderdelays")
def full_borders():
    try:
        data = get_combined_borders()

        return {
            "count": len(data),
            "borders": data,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve combined borders: {exc}",
        )
