class Corral < Formula
  desc "Manage QEMU and KubeVirt VMs/CTs - CLI, TUI, and web UI in one binary"
  homepage "https://github.com/tuna-os/corral"
  url "https://github.com/tuna-os/corral/archive/refs/tags/v0.2.0.tar.gz"
  sha256 "9c7ef3e2fdc80cee3324dbaec361cd0c7880822661f244a4a397387861cbdb9d"
  license "Apache-2.0"
  head "https://github.com/tuna-os/corral.git", branch: "main"

  depends_on "go" => :build

  def install
    ldflags = "-s -w -X github.com/tuna-os/corral/cmd.version=v#{version}"
    system "go", "build", *std_go_args(ldflags:)
    generate_completions_from_executable(bin/"corral", "completion")
  end

  test do
    assert_match "v#{version}", shell_output("#{bin}/corral version")
    # --demo runs against the built-in fake cluster, so the CLI is
    # exercisable end-to-end with no kubectl or cluster present.
    assert_match "web-prod", shell_output("#{bin}/corral list --demo")
  end
end
