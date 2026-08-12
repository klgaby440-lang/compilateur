# Fichier de configuration PyOxidizer pour SokoMaster Enterprise


def make_exe():
    dist = default_python_distribution()
    policy = dist.make_python_packaging_policy()

    # COMPATIBILITÉ WINDOWS :
    # "filesystem-relative:lib" isole les modules natifs et ressources dans le dossier "lib"
    policy.resources_location_fallback = "filesystem-relative:lib"
    policy.extension_module_filter = "all"

    config = dist.make_python_interpreter_config()
    config.run_module = "main"  # Point d'entrée principal (main.py)

    exe = dist.to_python_executable(
        name="SokoMaster",
        packaging_policy=policy,
        config=config,
    )
    return exe


def make_embedded_resources(exe):
    return exe.to_embedded_resources()


def make_install(exe):
    files = FileManifest()
    files.add_python_resource(".", exe)

    # Copie propre du dossier site-packages dans le sous-dossier lib/ du binaire
    if path_exists("site-packages"):
        files.add_path(path="site-packages", destination="lib")

    return files


# Enregistrement des cibles de build
register_target("exe", make_exe)
register_target("embedded_resources", make_embedded_resources, depends=["exe"])
register_target("install", make_install, depends=["exe"])

# Résolution globale des cibles
resolve_targets()
