# Shared helpers for the Visual Studio Code stable and Insiders casks
module VisualStudioCodeCask
  def self.apply(dsl, config)
    root = config.fetch(:root)
    executable = config.fetch(:executable)
    tunnel_executable = config.fetch(:tunnel_executable)
    desktop_file = config.fetch(:desktop_file)
    url_handler_file = config.fetch(:url_handler_file)
    desktop_content = desktop_entry(config)
    url_handler_content = url_handler_entry(config)

    dsl.instance_eval do
      depends_on formula: "jq"

      binary "#{root}/bin/#{executable}"
      binary "#{root}/bin/#{tunnel_executable}"
      bash_completion "#{root}/resources/completions/bash/#{executable}"
      zsh_completion "#{root}/resources/completions/zsh/_#{executable}"
      artifact "#{root}/#{desktop_file}",
               target: "#{Dir.home}/.local/share/applications/#{desktop_file}"
      artifact "#{root}/#{url_handler_file}",
               target: "#{Dir.home}/.local/share/applications/#{url_handler_file}"

      preflight_steps do
        move "VSCode-linux-*", root, source_glob: true
        product_json = "{{staged_path}}/#{root}/resources/app/product.json"
        run "{{HOMEBREW_PREFIX}}/bin/jq",
            args: ["del(.updateUrl) | .configurationDefaults[\"update.mode\"] = \"none\"", product_json],
            stdout_path: "product.json"
        run "/bin/mv", args: ["{{staged_path}}/product.json", product_json]

        mkdir_p ".local/share/applications", base: :home
        write_file desktop_file, desktop_content
        write_file url_handler_file, url_handler_content
        run "/bin/mv", args: ["{{staged_path}}/#{desktop_file}", "{{staged_path}}/#{url_handler_file}",
                              "{{staged_path}}/#{root}/"]
      end

      zap trash: config.fetch(:zap_paths)
    end
  end

  def self.desktop_entry(config)
    root = config.fetch(:root)
    executable = config.fetch(:executable)
    localized_names = config.fetch(:localized_names, []).map do |locale, name|
      "Name[#{locale}]=#{name}"
    end.join("\n")

    <<~EOS
      [Desktop Entry]
      Name=#{config.fetch(:desktop_name)}
      Comment=Code Editing. Redefined.
      GenericName=Text Editor
      Exec={{HOMEBREW_PREFIX}}/bin/#{executable} %F
      Icon={{staged_path}}/#{root}/resources/app/resources/linux/code.png
      Type=Application
      StartupNotify=false
      StartupWMClass=#{config.fetch(:startup_wm_class)}
      Categories=TextEditor;Development;IDE;
      MimeType=application/x-code-workspace;
      Actions=new-empty-window;
      Keywords=#{config.fetch(:keywords)};

      [Desktop Action new-empty-window]
      Name=New Empty Window
      #{localized_names}
      Exec={{HOMEBREW_PREFIX}}/bin/#{executable} --new-window %F
      Icon={{staged_path}}/#{root}/resources/app/resources/linux/code.png
    EOS
  end

  def self.url_handler_entry(config)
    root = config.fetch(:root)
    executable = config.fetch(:executable)

    <<~EOS
      [Desktop Entry]
      Name=#{config.fetch(:url_handler_name)}
      Comment=Code Editing. Redefined.
      GenericName=Text Editor
      Exec={{HOMEBREW_PREFIX}}/bin/#{executable} --open-url %U
      Icon={{staged_path}}/#{root}/resources/app/resources/linux/code.png
      Type=Application
      NoDisplay=true
      StartupNotify=true
      Categories=Utility;TextEditor;Development;IDE;
      MimeType=x-scheme-handler/#{config.fetch(:url_scheme)};
      Keywords=#{config.fetch(:keywords)};
    EOS
  end
end
