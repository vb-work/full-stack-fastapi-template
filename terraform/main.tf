# Variables for SSH key
variable "ssh_key_path" {
  description = "The path to private key"
  type        = string
}

# Security Group Configuration for Docker
resource "scaleway_instance_security_group" "docker_sg" {
  name = "docker-security-group"

  inbound_default_policy  = "drop"
  outbound_default_policy = "accept"

  inbound_rule {
    action   = "accept"
    port     = "22"
    ip_range = "0.0.0.0/0"
    protocol = "TCP"
  }

  inbound_rule {
    action   = "accept"
    port     = "80"
    ip_range = "0.0.0.0/0"
    protocol = "TCP"
  }
}

# IP Address Allocation
resource "scaleway_instance_ip" "docker_ip" {
  tags = ["docker"]
}

# Server Configuration
resource "scaleway_instance_server" "docker" {
  name         = "docker-instance"
  type         = "DEV1-S"
  image        = "ubuntu_focal"
  tags         = ["docker"]

  security_group_id = scaleway_instance_security_group.docker_sg.id

  root_volume {
    size_in_gb = 20
  }

  ip_id = scaleway_instance_ip.docker_ip.id

  # Provisioning Docker and Docker Compose
  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -y",
      "sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common",
      "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -",
      "sudo add-apt-repository 'deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable'",
      "sudo apt-get update -y",
      "sudo apt-get install -y docker-ce",
      "sudo systemctl start docker",
      "sudo systemctl enable docker",
      "sudo curl -L \"https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose",
      "sudo chmod +x /usr/local/bin/docker-compose",
    ]

    connection {
      type        = "ssh"
      user        = "root"
      private_key = file(var.ssh_key_path)
      host        = self.public_ip
    }
  }
}

# Output the instance IP
output "docker_instance_ip" {
  value = scaleway_instance_ip.docker_ip.address
}

