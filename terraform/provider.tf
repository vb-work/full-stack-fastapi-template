variable "project_id" {
  description = "The project id"
  type        = string
}

variable "access_key" {
  description = "The access key"
  type        = string
}

variable "secret_key" {
  description = "The secret key"
  type        = string
}

terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.0"  # Adjust the version as necessary
    }
  }
}

provider "scaleway" {
  project_id = var.project_id
  access_key = var.access_key
  secret_key = var.secret_key
  region     = "fr-par"
  zone       = "fr-par-1"
}
