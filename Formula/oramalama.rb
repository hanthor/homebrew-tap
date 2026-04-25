class Oramalama < Formula
  desc "Local AI coding assistant powered by RamaLama"
  homepage "https://github.com/hanthor/oramalama"
  license "Apache-2.0"
  version "0.1.2"

  on_macos do
    on_arm do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.2/oramalama_0.1.2_darwin_arm64.tar.gz"
      sha256 "77e42ef9f586f9fc105a30215ed8642ebbf2690fb38952e46c05ee4d8fa30f42"
    end
    on_intel do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.2/oramalama_0.1.2_darwin_amd64.tar.gz"
      sha256 "77e42ef9f586f9fc105a30215ed8642ebbf2690fb38952e46c05ee4d8fa30f42"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.2/oramalama_0.1.2_linux_arm64.tar.gz"
      sha256 "77e42ef9f586f9fc105a30215ed8642ebbf2690fb38952e46c05ee4d8fa30f42"
    end
    on_intel do
      url "https://github.com/hanthor/oramalama/releases/download/v0.1.2/oramalama_0.1.2_linux_amd64.tar.gz"
      sha256 "77e42ef9f586f9fc105a30215ed8642ebbf2690fb38952e46c05ee4d8fa30f42"
    end
  end

  depends_on "ramalama"
  depends_on "gum"
  depends_on "jq"

  def install
    bin.install "oramalama"
  end

  test do
    assert_match /^oramalama version/, shell_output("#{bin}/oramalama -version")
  end
end
