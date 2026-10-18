# Shared release metadata for the ASUS daemon and GUI casks
module AsusctlCask
  RELEASES_URL = "https://api.github.com/repos/daegalus/linux-app-builds/releases/latest"

  CHECKSUMS = {
    arm:          "66b7e0c8c358ad2281c806240a410be1c0e61c3c182b05408490f92de779bb9d",
    intel:        "f05fbc48e5971649685d9269a4e7d6c835e3163e8946c4a3cebc49a5cc647cc5",
    arm64_linux:  "66b7e0c8c358ad2281c806240a410be1c0e61c3c182b05408490f92de779bb9d",
    x86_64_linux: "f05fbc48e5971649685d9269a4e7d6c835e3163e8946c4a3cebc49a5cc647cc5",
  }.freeze

  def self.release_url(version_parts, arch)
    release_tag = "asusctl-#{version_parts.first}-#{version_parts.second}"
    release_root = "asusctl-#{version_parts.first}-ubuntu-22.04-#{arch}"

    "https://github.com/daegalus/linux-app-builds/releases/download/#{release_tag}/#{release_root}.tar.gz"
  end

  def self.version_from_release(json)
    tag = json["tag_name"].to_s
    match = tag.match(/^asusctl-(\d+(?:\.\d+)+)-(\d+)$/)
    return if match.nil?

    "#{match[1]},#{match[2]}"
  end
end
