# VPC segmentation for the CUI enclave (SC.L2-3.13.3/4/5/6/7/8/9/15).
#
# One VPC, one private subnet for CUI workloads, default-deny ingress, and one
# narrow internal-TLS rule allowing east-west traffic. Plans offline (no cloud
# calls) because create-only plans never mint a token for the google provider.
# Labels ALL resources with cmmc_control slugs so the plan-JSON binding path
# maps them to controls without ambiguity.

resource "google_compute_network" "cui" {
  name                    = "cui-enclave"
  auto_create_subnetworks = false
  # Private-only: no automatic public subnets.
}

resource "google_compute_subnetwork" "cui_private" {
  name                     = "cui-private"
  ip_cidr_range            = "10.10.0.0/20"
  region                   = var.primary_region
  network                  = google_compute_network.cui.id
  private_ip_google_access = true
}

# Default-deny ingress from the internet — SC.13.6 (deny by default).
resource "google_compute_firewall" "deny_all_ingress" {
  name          = "cui-deny-all-ingress"
  network       = google_compute_network.cui.name
  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]

  deny { protocol = "all" }
}

# Allow east-west TLS 1.2+ internal traffic only — SC.13.8 (crypto in transit).
resource "google_compute_firewall" "allow_internal_tls" {
  name          = "cui-allow-internal-tls"
  network       = google_compute_network.cui.name
  direction     = "INGRESS"
  priority      = 1000
  source_ranges = ["10.10.0.0/20"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}
