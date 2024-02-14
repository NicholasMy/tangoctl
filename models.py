from typing import Dict, Optional
from pydantic import BaseModel


class TangoNode(BaseModel):
    fqdn: str
    ssh_key_path: Optional[str] = None
    ssh_username: Optional[str] = None
    volumes_path: Optional[str] = None


class Config(BaseModel):
    docker_hub_org: str
    ssh_key_path: str
    ssh_username: str
    volumes_path: str
    tango_nodes: Dict[str, TangoNode]  # name -> TangoNode
