packer {
  required_plugins {
    docker = {
      source  = "github.com/hashicorp/docker"
      version = ">= 1.1.0"
    }
  }
}

variable "image_name" {
  type    = string
  default = "pra/flask-sqlite"
}

variable "image_tag" {
  type    = string
  default = "1.1"
}

source "docker" "flask" {
  image  = "python:3.12-slim"
  commit = true
}

build {
  name    = "pra-flask-sqlite"
  sources = ["source.docker.flask"]

  # Copie le code dans l'image
  provisioner "file" {
    source      = "app/"
    destination = "/opt/app"
  }

  # Installe les dépendances
  provisioner "shell" {
    inline = [
      "set -eux",
      "python -m pip install --no-cache-dir --upgrade pip",
      "pip install --no-cache-dir -r /opt/app/requirements.txt",
      "mkdir -p /data",
      "chmod 777 /data",
      "echo 'Packer build done.'"
    ]
  }

  # Tag final de l'image
  post-processor "docker-tag" {
    repository = var.image_name
    tags       = [var.image_tag]
  }
}
