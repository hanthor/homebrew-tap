class Oramalama < Formula
  desc "Local AI coding assistant powered by RamaLama"
  homepage "https://github.com/hanthor/oramalama"
  url "https://github.com/hanthor/oramalama/releases/download/#{version}/oramalama_#{version}_#{os}_#{hardware_arch}.tar.gz"
  version "{{VERSION}}"
  sha256 "{{SHA256}}"
  license "Apache-2.0"

  depends_on "ramalama"
  depends_on "gum"
  depends_on "jq"

  def install
    bin.install "oramalama"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/oramalama --version")
  end

  private

  def os
    OS.mac? ? "darwin" : "linux"
  end

  def hardware_arch
    Hardware::CPU.arm? ? "arm64" : "amd64"
  end
end
