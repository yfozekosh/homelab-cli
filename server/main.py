"""
FastAPI Server for Homelab Management
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .config import Config
from .plug_service import PlugService
from .server_service import ServerService
from .power_service import PowerControlService
from .status_service import StatusService

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# API Key Security
API_KEY = os.getenv("API_KEY", "homelab-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key"""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
    return api_key


# Pydantic models
class PlugCreate(BaseModel):
    name: str
    ip: str


class PlugRemove(BaseModel):
    name: str


class ServerCreate(BaseModel):
    name: str
    hostname: str
    mac: Optional[str] = None
    plug: Optional[str] = None


class ServerUpdate(BaseModel):
    name: str
    hostname: Optional[str] = None
    mac: Optional[str] = None
    plug: Optional[str] = None


class PlugUpdate(BaseModel):
    name: str
    ip: str


class ServerRemove(BaseModel):
    name: str


class PowerAction(BaseModel):
    name: str


class ElectricityPrice(BaseModel):
    price: float  # Price per kWh


# Global services
config: Config = None
plug_service: PlugService = None
server_service: ServerService = None
power_service: PowerControlService = None
status_service: StatusService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    global config, plug_service, server_service, power_service, status_service

    logger.info("Starting Homelab Server...")

    # Initialize services
    config_path = Path(os.getenv("CONFIG_PATH", "/app/data/config.json"))
    config = Config(config_path)
    plug_service = PlugService()
    server_service = ServerService()
    power_service = PowerControlService(plug_service, server_service)
    status_service = StatusService(config, plug_service, server_service)

    logger.info("Server initialized successfully")

    yield

    logger.info("Shutting down Homelab Server...")


app = FastAPI(
    title="Homelab Management API",
    description="REST API for managing smart plugs and servers",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/status", dependencies=[Depends(verify_api_key)])
async def get_status():
    """Get comprehensive status of all servers and plugs"""
    try:
        status = await status_service.get_all_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/plugs", dependencies=[Depends(verify_api_key)])
async def list_plugs():
    """List all configured plugs"""
    return {"plugs": config.list_plugs()}


@app.post("/plugs", dependencies=[Depends(verify_api_key)])
async def add_plug(plug: PlugCreate):
    """Add a new plug"""
    try:
        config.add_plug(plug.name, plug.ip)
        return {"message": f"Plug '{plug.name}' added successfully"}
    except Exception as e:
        logger.error(f"Failed to add plug: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/plugs", dependencies=[Depends(verify_api_key)])
async def update_plug(plug: PlugUpdate):
    """Update a plug IP address"""
    try:
        if config.update_plug(plug.name, plug.ip):
            return {"message": f"Plug '{plug.name}' updated successfully"}
        raise HTTPException(status_code=404, detail=f"Plug '{plug.name}' not found")
    except Exception as e:
        logger.error(f"Failed to update plug: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/plugs", dependencies=[Depends(verify_api_key)])
async def remove_plug(plug: PlugRemove):
    """Remove a plug"""
    if config.remove_plug(plug.name):
        return {"message": f"Plug '{plug.name}' removed successfully"}
    raise HTTPException(status_code=404, detail=f"Plug '{plug.name}' not found")


@app.get("/plugs/{name}/status", dependencies=[Depends(verify_api_key)])
async def get_plug_status(name: str):
    """Get plug status"""
    plug = config.get_plug(name)
    if not plug:
        raise HTTPException(status_code=404, detail=f"Plug '{name}' not found")

    try:
        status = await plug_service.get_status(plug["ip"])
        power = await plug_service.get_power(plug["ip"])
        return {"name": name, "status": status, "power": power}
    except Exception as e:
        logger.error(f"Failed to get plug status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plugs/{name}/on", dependencies=[Depends(verify_api_key)])
async def turn_plug_on(name: str):
    """Turn on a plug"""
    plug = config.get_plug(name)
    if not plug:
        raise HTTPException(status_code=404, detail=f"Plug '{name}' not found")

    try:
        await plug_service.turn_on(plug["ip"])
        return {"message": f"Plug '{name}' turned on"}
    except Exception as e:
        logger.error(f"Failed to turn on plug: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plugs/{name}/off", dependencies=[Depends(verify_api_key)])
async def turn_plug_off(name: str):
    """Turn off a plug"""
    plug = config.get_plug(name)
    if not plug:
        raise HTTPException(status_code=404, detail=f"Plug '{name}' not found")

    try:
        await plug_service.turn_off(plug["ip"])
        return {"message": f"Plug '{name}' turned off"}
    except Exception as e:
        logger.error(f"Failed to turn off plug: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/servers", dependencies=[Depends(verify_api_key)])
async def list_servers():
    """List all configured servers"""
    servers = config.list_servers()

    # Add resolved IP and online status
    result = {}
    for name, server in servers.items():
        result[name] = {
            **server,
            "ip": server_service.resolve_hostname(server["hostname"]),
            "online": server_service.ping(server["hostname"]),
        }

    return {"servers": result}


@app.get("/ssh-healthcheck", dependencies=[Depends(verify_api_key)])
async def ssh_healthcheck():
    """Check SSH connectivity and sudo permissions for all servers"""
    servers = config.list_servers()
    results = []

    for name, server in servers.items():
        hostname = server["hostname"]
        result = {
            "server": name,
            "hostname": hostname,
            "ssh_works": False,
            "sudo_works": False,
            "error": None,
        }

        try:
            # Test SSH connectivity
            ssh_ok = server_service.test_ssh_connection(hostname)
            result["ssh_works"] = ssh_ok

            if ssh_ok:
                # Test sudo permissions
                sudo_ok = server_service.test_sudo_poweroff(hostname)
                result["sudo_works"] = sudo_ok

        except Exception as e:
            result["error"] = str(e)

        results.append(result)

    return {"results": results}


@app.post("/servers", dependencies=[Depends(verify_api_key)])
async def add_server(server: ServerCreate):
    """Add a new server"""
    try:
        config.add_server(server.name, server.hostname, server.mac, server.plug)
        return {"message": f"Server '{server.name}' added successfully"}
    except Exception as e:
        logger.error(f"Failed to add server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/servers", dependencies=[Depends(verify_api_key)])
async def update_server(server: ServerUpdate):
    """Update server configuration"""
    try:
        if config.update_server(server.name, server.hostname, server.mac, server.plug):
            return {"message": f"Server '{server.name}' updated successfully"}
        raise HTTPException(status_code=404, detail=f"Server '{server.name}' not found")
    except Exception as e:
        logger.error(f"Failed to update server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/servers", dependencies=[Depends(verify_api_key)])
async def remove_server(server: ServerRemove):
    """Remove a server"""
    if config.remove_server(server.name):
        return {"message": f"Server '{server.name}' removed successfully"}
    raise HTTPException(status_code=404, detail=f"Server '{server.name}' not found")


@app.get("/servers/{name}", dependencies=[Depends(verify_api_key)])
async def get_server(name: str):
    """Get server details"""
    server = config.get_server(name)
    if not server:
        raise HTTPException(status_code=404, detail=f"Server '{name}' not found")

    return {
        "name": name,
        **server,
        "ip": server_service.resolve_hostname(server["hostname"]),
        "online": server_service.ping(server["hostname"]),
    }


@app.post("/power/on", dependencies=[Depends(verify_api_key)])
async def power_on_server(action: PowerAction):
    """Power on a server with SSE streaming"""
    server = config.get_server(action.name)
    if not server:
        raise HTTPException(status_code=404, detail=f"Server '{action.name}' not found")

    if not server.get("plug"):
        raise HTTPException(
            status_code=400, detail=f"No plug associated with server '{action.name}'"
        )

    if not server.get("mac"):
        raise HTTPException(
            status_code=400,
            detail=f"No MAC address configured for server '{action.name}'",
        )

    plug = config.get_plug(server["plug"])
    if not plug:
        raise HTTPException(
            status_code=404, detail=f"Plug '{server['plug']}' not found"
        )

    async def event_generator():
        """Generate SSE events for real-time progress"""
        log_queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def progress_callback(msg: str):
            # Schedule task in the event loop from sync callback
            asyncio.run_coroutine_threadsafe(log_queue.put(msg), loop)

        # Start power on operation in background
        async def run_power_on():
            try:
                result = await power_service.power_on(
                    server, plug["ip"], progress_callback
                )
                await log_queue.put({"type": "complete", "result": result})
            except Exception as e:
                logger.error(f"Failed to power on server: {e}")
                await log_queue.put({"type": "error", "message": str(e)})

        task = asyncio.create_task(run_power_on())

        # Stream logs as they arrive
        while True:
            try:
                msg = await asyncio.wait_for(log_queue.get(), timeout=0.5)

                if isinstance(msg, dict):
                    if msg.get("type") == "complete":
                        import json

                        yield f"data: {json.dumps(msg['result'])}\n\n"
                        break
                    elif msg.get("type") == "error":
                        yield f"event: error\ndata: {msg['message']}\n\n"
                        break
                else:
                    # Regular log message
                    import json

                    yield f"event: log\ndata: {json.dumps({'message': msg})}\n\n"

            except asyncio.TimeoutError:
                # Keep connection alive
                yield f": keepalive\n\n"

        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/power/off", dependencies=[Depends(verify_api_key)])
async def power_off_server(action: PowerAction):
    """Power off a server with SSE streaming"""
    server = config.get_server(action.name)
    if not server:
        raise HTTPException(status_code=404, detail=f"Server '{action.name}' not found")

    if not server.get("plug"):
        raise HTTPException(
            status_code=400, detail=f"No plug associated with server '{action.name}'"
        )

    plug = config.get_plug(server["plug"])
    if not plug:
        raise HTTPException(
            status_code=404, detail=f"Plug '{server['plug']}' not found"
        )

    async def event_generator():
        """Generate SSE events for real-time progress"""
        log_queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def progress_callback(msg: str):
            # Schedule task in the event loop from sync callback
            asyncio.run_coroutine_threadsafe(log_queue.put(msg), loop)

        # Start power off operation in background
        async def run_power_off():
            try:
                result = await power_service.power_off(
                    server, plug["ip"], progress_callback
                )
                await log_queue.put({"type": "complete", "result": result})
            except Exception as e:
                logger.error(f"Failed to power off server: {e}")
                await log_queue.put({"type": "error", "message": str(e)})

        task = asyncio.create_task(run_power_off())

        # Stream logs as they arrive
        while True:
            try:
                msg = await asyncio.wait_for(log_queue.get(), timeout=0.5)

                if isinstance(msg, dict):
                    if msg.get("type") == "complete":
                        import json

                        yield f"data: {json.dumps(msg['result'])}\n\n"
                        break
                    elif msg.get("type") == "error":
                        yield f"event: error\ndata: {msg['message']}\n\n"
                        break
                else:
                    # Regular log message
                    import json

                    yield f"event: log\ndata: {json.dumps({'message': msg})}\n\n"

            except asyncio.TimeoutError:
                # Keep connection alive
                yield f": keepalive\n\n"

        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/settings/electricity-price", dependencies=[Depends(verify_api_key)])
async def set_electricity_price(price_data: ElectricityPrice):
    """Set electricity price per kWh"""
    config.set_electricity_price(price_data.price)
    return {
        "message": f"Electricity price set to {price_data.price}",
        "price": price_data.price,
    }


@app.get("/settings/electricity-price", dependencies=[Depends(verify_api_key)])
async def get_electricity_price():
    """Get current electricity price per kWh"""
    price = config.get_electricity_price()
    return {"price": price}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
