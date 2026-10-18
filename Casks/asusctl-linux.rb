require_relative "../lib/asusctl_cask"

cask "asusctl-linux" do
  arch arm: "arm64", intel: "amd64"
  os linux: "linux"

  version "6.3.8,3"
  sha256 **AsusctlCask::CHECKSUMS

  url AsusctlCask.release_url(version.csv, arch)
  name "asusctl"
  desc "ASUS laptop control CLI and immutable-friendly system daemon payload"
  homepage "https://gitlab.com/asus-linux/asusctl"

  livecheck do
    url AsusctlCask::RELEASES_URL
    strategy :json do |json|
      AsusctlCask.version_from_release(json)
    end
  end

  binary "asusctl/usr/bin/asusctl"
  binary "asusctl/usr/bin/asusd"
  binary "asusctl/usr/bin/asus-shutdown"

  preflight_steps do
    move "asusctl-*-ubuntu-22.04-*", "asusctl", source_glob: true
  end

  postflight_steps do
    # Generate files in the existing stage without predeclaring them as directories.
    run "/bin/sed", args:        ["-e", "/^Environment=ASUSD_EXEC=/d",
                                  "-e", "s|ExecStart=${ASUSD_EXEC}|ExecStart=/opt/ublue-asusctl/bin/asusd|",
                                  "{{staged_path}}/asusctl/usr/lib/systemd/system/asusd.service"],
                    stdout_path: "asusd.service"
    run "/bin/sed", args:        ["-e", "/^Environment=ASUS_SHUTDOWN_EXEC=/d",
                                  "-e",
                                  "s|ExecStart=${ASUS_SHUTDOWN_EXEC}|ExecStart=/opt/ublue-asusctl/bin/asus-shutdown|",
                                  "{{staged_path}}/asusctl/usr/lib/systemd/system/asus-shutdown.service"],
                    stdout_path: "asus-shutdown.service"
    write_file "asusd.env", <<~EOS
      ASUSD_DATA_DIR=/opt/ublue-asusctl/share/asusd
      ASUSCTL_AURA_SUPPORT_PATH=/opt/ublue-asusctl/share/asusd/aura_support.ron
      ASUSCTL_DATA_DIRS=/opt/ublue-asusctl/share
    EOS
    run "/bin/sh", args: ["-eu", "-c", <<~SH, "--", "{{staged_path}}"], sudo: true
      PATH=/usr/sbin:/usr/bin:/bin
      stage=$1
      root=/opt/ublue-asusctl
      install -d "$root/bin" "$root/share/asusd" /etc/systemd/system /etc/udev/rules.d /etc/dbus-1/system.d /etc/asusd
      install -Dm0755 "$stage/asusctl/usr/bin/asusd" "$root/bin/asusd"
      install -Dm0755 "$stage/asusctl/usr/bin/asus-shutdown" "$root/bin/asus-shutdown"
      cp -a "$stage/asusctl/usr/share/asusd/." "$root/share/asusd"
      install -Dm0644 "$stage/asusd.service" /etc/systemd/system/asusd.service
      install -Dm0644 "$stage/asus-shutdown.service" /etc/systemd/system/asus-shutdown.service
      install -Dm0644 "$stage/asusctl/usr/lib/udev/rules.d/99-asusd.rules" /etc/udev/rules.d/99-asusd.rules
      install -Dm0644 "$stage/asusctl/usr/share/dbus-1/system.d/asusd.conf" /etc/dbus-1/system.d/asusd.conf
      install -Dm0644 "$stage/asusd.env" /etc/asusd/asusd.env

      if command -v getenforce >/dev/null && [ "$(getenforce)" != Disabled ]; then
        if command -v semanage >/dev/null; then
          semanage fcontext -a -t bin_t "$root/bin(/.*)?" || semanage fcontext -m -t bin_t "$root/bin(/.*)?"
        elif command -v chcon >/dev/null; then
          chcon -R -t bin_t "$root/bin"
        fi
        if command -v restorecon >/dev/null; then
          restorecon -RFv "$root" /etc/systemd/system /etc/udev/rules.d /etc/dbus-1/system.d /etc/asusd
        fi
      fi
      if command -v systemctl >/dev/null; then systemctl daemon-reload || true; fi
      if command -v udevadm >/dev/null; then udevadm control --reload || true; fi
    SH
  end

  uninstall_preflight_steps do
    run "/bin/sh", args: ["-eu", "-c", <<~'SH'], sudo: true
      PATH=/usr/sbin:/usr/bin:/bin
      if command -v systemctl >/dev/null; then
        systemctl disable --now asus-shutdown.service || true
        systemctl disable --now asusd.service || true
      fi
      selinux=Disabled
      if command -v getenforce >/dev/null; then selinux=$(getenforce); fi
      if [ "$selinux" != Disabled ] && command -v semanage >/dev/null; then
        semanage fcontext -d "/opt/ublue-asusctl/bin(/.*)?" || true
      fi
      rm -f /etc/systemd/system/asusd.service /etc/systemd/system/asus-shutdown.service \
        /etc/udev/rules.d/99-asusd.rules /etc/dbus-1/system.d/asusd.conf /etc/asusd/asusd.env
      rm -rf /opt/ublue-asusctl
      rmdir /etc/asusd 2>/dev/null || true
      if command -v systemctl >/dev/null; then systemctl daemon-reload || true; fi
      if command -v udevadm >/dev/null; then udevadm control --reload || true; fi
      if [ "$selinux" != Disabled ] && command -v restorecon >/dev/null; then
        restorecon -RFv /opt /var/opt || true
      fi
    SH
  end

  caveats <<~EOS
    Root-only daemon files were installed to:
      /opt/ublue-asusctl
      /etc/asusd/asusd.env
      /etc/systemd/system/asusd.service
      /etc/systemd/system/asus-shutdown.service
      /etc/udev/rules.d/99-asusd.rules
      /etc/dbus-1/system.d/asusd.conf

    On Aurora, Bluefin and Bazzite, /opt resolves into writable /var storage, so the
    daemon payload does not depend on a writable /usr tree.

    To activate the system services:
      sudo systemctl enable --now asusd.service asus-shutdown.service
      sudo udevadm control --reload
      sudo udevadm trigger

    For the GUI and user daemon:
      brew install --cask rog-control-center-linux
  EOS
end
