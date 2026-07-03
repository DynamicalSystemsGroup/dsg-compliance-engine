# `terraform test` for the Tier 1 enclave — runs entirely on mock providers,
# so `plan` and (mocked) `apply` execute with NO credentials and NO cloud.
#
# Run: terraform -chdir=terraform/tier1 test

mock_provider "google" {}
mock_provider "googleworkspace" {}
mock_provider "null" {}

variables {
  # Exercise the real googleworkspace_* resources under the mock provider.
  enable_workspace = true
  primary_region   = "us-central1"
}

# The HCL plans cleanly with mock providers (no cloud).
run "plan_builds_enclave" {
  command = plan

  assert {
    condition     = google_kms_key_ring.cui.location == "us"
    error_message = "CMEK keyring must be in the US multi-region."
  }

  assert {
    condition     = length(terraform_data.cmmc_tag) == 11
    error_message = "Expected one control tag per tier1.ttl module (11: 10 tier-1 + VPC_Segmentation)."
  }
}

# A mocked apply completes end-to-end with no cloud.
run "apply_is_clean" {
  command = apply

  assert {
    condition     = google_kms_crypto_key.cui_cmek.labels["cmmc_control"] == "sc-l2-3-13-11"
    error_message = "CMEK key must carry its cmmc_control label."
  }
}

# Residency guard: a US region keeps the org-policy allow-list on us-locations.
run "us_region_allows_us_locations" {
  command = plan

  assert {
    condition     = contains(google_org_policy_policy.resource_locations.spec[0].rules[0].values[0].allowed_values, "in:us-locations")
    error_message = "US region must pin resourceLocations to us-locations."
  }
}
