import asyncio
import random
from datetime import datetime, timezone

from app.websocket.manager import manager

CATEGORIES = ["temperature", "humidity", "pressure", "cpu_load", "memory_usage", "network_io"]
THRESHOLDS = {
    "temperature": 80.0,
    "humidity": 90.0,
    "pressure": 1050.0,
    "cpu_load": 85.0,
    "memory_usage": 90.0,
    "network_io": 950.0,
}


async def generate_data() -> dict:
    category = random.choice(CATEGORIES)
    value = round(random.uniform(10, 100), 2)
    threshold = THRESHOLDS[category]
    return {
        "title": f"Realtime {category.replace('_', ' ').title()}",
        "value": value,
        "category": category,
        "is_anomaly": value > threshold,
        "threshold": threshold,
        "source": "simulator",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def run_simulator() -> None:
    while True:
        if manager.connection_count > 0:
            data = await generate_data()
            await manager.broadcast({"type": "realtime_data", "data": data})
        await asyncio.sleep(1)
