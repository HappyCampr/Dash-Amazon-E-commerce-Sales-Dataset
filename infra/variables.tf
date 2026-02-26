variable "project_id" { type = string }
variable "region"     { type = string  default = "us-central1" }

# GitHub Actions will produce this:
# us-central1-docker.pkg.dev/PROJECT_ID/dash/dashapp:<gitsha>
variable "image" { type = string }

variable "service_name" {
  type    = string
  default = "dash-portfolio"
}

variable "allow_unauthenticated" {
  type    = bool
  default = true
}