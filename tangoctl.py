import argparse
import subprocess
from datetime import datetime
from functools import lru_cache
from typing import Dict, List
import yaml
from models import Config, TangoNode


@lru_cache()
def get_config() -> Config:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return Config(**config)


def parse_args_to_config() -> argparse.Namespace:
    # Parse arguments, modify the config if necessary, return the args
    config = get_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", type=str, help="Override the configuration's Docker Hub organization")
    parser.add_argument("--ssh-key-path", type=str, help="Override the configuration's default SSH key path")
    parser.add_argument("--ssh-username", type=str, help="Override the configuration's default SSH username")

    sub_parsers = parser.add_subparsers(dest="command", required=True)

    build_parser = sub_parsers.add_parser("build", help="Build a Docker image locally without deploying it")
    build_parser.add_argument("dockerfile", type=str,
                              help="Path to a local directory containing a Dockerfile or a URL to a Dockerfile")
    build_parser.add_argument("image_name", type=str, help="Name of the Docker image to build, "
                                                           "without an org or tag")

    deploy_parser = sub_parsers.add_parser("deploy", help="Deploy a Docker image to a Tango node")
    deploy_parser.add_argument("image_name", type=str, help="Name of the Docker image to deploy, "
                                                            "including an org and tag")
    deploy_parser.add_argument("tango_node", type=str, help="Name of the Tango node(s) to deploy to, "
                                                            "separated by commas (no spaces), or 'all' for all nodes")

    aio_parser = sub_parsers.add_parser("aio", help="All-in-one: Build and deploy a Docker image to all Tango nodes")
    aio_parser.add_argument("dockerfile", type=str,
                            help="Path to a local directory containing a Dockerfile or a URL to a Dockerfile")
    aio_parser.add_argument("image_name", type=str, help="Name of the Docker image to build and deploy, "
                                                         "without an org or tag")

    args = parser.parse_args()
    if args.org:
        config.docker_hub_org = args.org
    if args.ssh_key_path:
        config.ssh_key_path = args.ssh_key_path
    if args.ssh_username:
        config.ssh_username = args.ssh_username
    return args


def get_tango_node(name: str) -> TangoNode:
    return get_config().tango_nodes[name]


def node_list_to_nodes(node_list: str) -> List[TangoNode]:
    # Convert a comma-separated list of node names to a list of TangoNode objects
    # 'all' is a special case that returns all nodes
    if node_list == "all":
        return list(get_config().tango_nodes.values())
    else:
        return [get_tango_node(name) for name in node_list.split(",")]


def get_date_time_stamp() -> str:
    # Used for tagging Docker images
    return datetime.now().strftime("%Y.%m.%d.%H%M%S")


def build_docker_image_from_dockerfile(dockerfile: str, image_name: str) -> str:
    # Build a Docker image locally and name it, returns the image name with the latest tag
    # `dockerfile` can be a path to a local directory containing a Dockerfile or a URL to a Dockerfile
    # `image_name` should be formatted like `org/name` and NOT include a tag
    assert ":" not in image_name, "image_name should not include a tag"
    assert image_name.count("/") == 1, "image_name should include exactly one slash (for the org)"
    timestamp_tag: str = get_date_time_stamp()
    image_name_timestamp: str = f"{image_name}:{timestamp_tag}"
    image_name_latest: str = f"{image_name}:latest"
    # Build and tag with timestamp
    subprocess.run(["docker", "build", "-t", image_name_timestamp, dockerfile])
    # Tag as latest
    subprocess.run(["docker", "tag", image_name_timestamp, image_name_latest])
    return image_name_latest


def push_docker_image(image_name: str):
    # Push a docker image to Docker Hub
    # Image name should be formatted like `org/name:tag` (e.g., `myorg/myimage:latest`)
    subprocess.run(["docker", "push", image_name])


def run_command_on_tango_node(command: str, tango_node: TangoNode):
    ssh_key_path: str = tango_node.ssh_key_path if tango_node.ssh_key_path else get_config().ssh_key_path
    ssh_username: str = tango_node.ssh_username if tango_node.ssh_username else get_config().ssh_username
    ssh_user_host: str = f"{ssh_username}@{tango_node.fqdn}"

    proc = subprocess.run(
        ["ssh", "-o", "IdentitiesOnly=yes", "-i", ssh_key_path, ssh_user_host, command])
    if proc.returncode != 0:
        raise Exception(f"Command failed on {tango_node.fqdn}: {command}. Status code: {proc.returncode}")


def deploy_docker_image(image_name: str, tango_node: TangoNode):
    # Download a docker image to a Tango node
    # Image name should be formatted like `org/name:tag` (e.g., `myorg/myimage:latest`)
    print(f"Deploying image {image_name} to {tango_node.fqdn}...")
    image_name_without_org: str = image_name.split("/")[1]
    run_command_on_tango_node(f"docker pull {image_name}", tango_node)
    run_command_on_tango_node(f"docker tag {image_name} {image_name_without_org}", tango_node)
    run_command_on_tango_node(f"docker image rm {image_name}", tango_node)
    print(f"Finished deploying image {image_name} to {tango_node.fqdn}")


def build(args: argparse.Namespace) -> str:
    # Build a Docker image locally and return the image name with the latest tag
    org: str = get_config().docker_hub_org
    image_name: str = f"{org}/{args.image_name}"
    assert "/" not in args.image_name, ("image_name, as an argument, should not include a slash "
                                        "(do not specify an org here, use --org instead)")
    return build_docker_image_from_dockerfile(args.dockerfile, image_name)


def deploy(args: argparse.Namespace):
    # Deploy a Docker image from Docker Hub to a Tango node
    target_nodes = node_list_to_nodes(args.tango_node)
    image: str = f"{args.image_name}"
    for node in target_nodes:
        deploy_docker_image(image, node)


def aio(args: argparse.Namespace):
    # All-in-one: Build, push, and deploy a Docker image to all Tango nodes
    image_name_latest: str = build(args)
    push_docker_image(image_name_latest)
    target_nodes = list(get_config().tango_nodes.values())
    for node in target_nodes:
        deploy_docker_image(image_name_latest, node)


def main():
    get_config()  # Cache the initial config
    args = parse_args_to_config()

    commands: Dict[str, callable] = {
        "build": build,
        "deploy": deploy,
        "aio": aio,
    }

    commands[args.command](args)


if __name__ == '__main__':
    main()
