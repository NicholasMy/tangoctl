# Tangoctl

A command-line utility for managing [Tango](https://github.com/UB-CSE-IT/Tango) Docker images
for [Autolab](https://github.com/UB-CSE-IT/Autolab).

Written in Python 3.8 to maintain compatibility with older versions of Ubuntu.

## Features

- Build Docker images from a Dockerfile and tag them properly for uploading to Docker Hub
- Deploy images from Docker Hub to all Tango servers in the cluster
- Build, upload, and deploy with one command!

## Installation

- Clone this repo to the Autolab server or your local machine: `git clone https://github.com/NicholasMy/tangoctl.git`
- Cd into the project: `cd tangoctl`
- Create a virtual environment: `python3 -m venv venv`
- Activate the virtual environment: `source venv/bin/activate`
- Install the requirements: `pip install -r requirements.txt`
- Optionally, "install" this tool with `sudo bash install.sh` from the `tangoctl` directory.
    - This will allow you to run `tangoctl` from anywhere by dynamically generating `tangoctl_installed.py` using the
      venv's executable path and creating a symlink in /usr/local/bin.
- Ensure the permissions are correct: `sudo chmod 755 tangoctl.py`. The install script does this automatically.

## Configuration

- Copy the template config file to create your own within the project directory: `cp config.yaml.template config.yaml`
- `docker_hub_org` is the Docker Hub organization to use when building and uploading images
- `ssh_key_path` is the path to the SSH key to use when deploying images
- `ssh_username` is the username to use when deploying images
- `tango_nodes` is a list of Tango nodes to deploy to. Each node must include `fqdn`, the fully-qualified domain name,
  and can optionally include `ssh_key_path` and `ssh_username` as per-node overrides.

## Usage

In general, commands are formatted as:

`tangoctl [config_overrides] <command> <options...>`

Arguments in \[square brackets\] are optional. Arguments in \<angle brackets\> are required.

Run `tangoctl [command] -h` to see a list of commands and options.

### Configuration override options:

All of these are optional. If not provided, the values in the configuration file will be used.
Due to the way Python's argparse library works, these must be provided before the command.

- `--org` - Override the configuration's Docker Hub organization
- `--ssh-key-path` - Override the configuration's default SSH key path
- `--ssh-username` - Override the configuration's default SSH username

E.g., `tangoctl --org myorg --ssh-username myuser deploy ...`

### Build an image

`tangoctl [config_overrides] build <dockerfile> <image_name>`

Builds a Docker image from a Dockerfile (local or URL) locally, and properly tags it with a datestamp and latest tag.

- `dockerfile` is the path to a directory containing a Dockerfile OR a URL to a Dockerfile
- `image_name` is the name of the image to build and deploy, without an org or tag, e.g. `cse_116`

### Upload an image

This is not provided as a standalone command by Tangoctl because it's already provided by Docker.

Use `docker push <image_name>` to upload an image to Docker Hub. `image_name` should include an org and a tag. You'll
need to be logged in.

If you use the All-in-one (AIO) command, this action will be performed automatically.

### Deploy an image

`tangoctl [config_overrides] deploy <image_name> <tango_node(s)>`

Download an image from Docker Hub and deploy it to the specified Tango node(s). This will handle removing the org for
cleanliness on Autolab.

- `image_name` is the name of the image to deploy, including an org and a tag.
- `tango_node(s)` can be one or more Tango nodes, separated by commas, or 'all'. These are configured in the config
  file.

### All-in-one (AIO)

`tangoctl [config_overrides] aio <dockerfile> <image_name>`

Build, upload, and deploy an image in one command!

This builds a Docker image locally, uploads the image to Docker Hub, and deploys it to all Tango nodes in the cluster.

Just like `build`:

- `dockerfile` is the path to a directory containing a Dockerfile OR a URL to a Dockerfile
- `image_name` is the name of the image to build and deploy, without an org or tag, e.g. `cse_116`

Because this pushes to Docker Hub, it requires being logged in. Use `docker login` and `docker logout` to manage your
authentication.

### View Docker images

`tangoctl [config_overrides] images`

Display which Docker images are installed on each Tango node.

### View Docker volumes

`tangoctl [config_overrides] volumes`

Display the contents of the Tango volumes directory on each Tango node.