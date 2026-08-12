# Fichier de configuration PyOxidizer pour SokoMaster Enterprise


def make_exe():
    dist = default_python_distribution()
    policy = dist.make_python_packaging_policy()

    # Tente d'embarquer le maximum de ressources directement en mémoire RAM
    policy.resources_location = "in-memory"

    # COMPATIBILITÉ WINDOWS :
    # Isole les modules C natifs (_asyncio, _sqlite3, etc.) dans le dossier "lib"
    policy.resources_location_fallback = "filesystem-relative:lib"

    # Prise en charge de toutes les extensions natives C/.pyd
    policy.extension_module_filter = "all"

    config = dist.make_python_interpreter_config()
    config.run_module = "main"  # Point d'entrée principal (main.py)

    exe = dist.to_python_executable(
        name="SokoMaster",
        packaging_policy=policy,
        config=config,
    )

    # --------------------------------------------------------------------------
    # AJOUT ESSENTIEL : Empaquetage automatique des dépendances requirements.txt
    # --------------------------------------------------------------------------
    exe.add_python_resources(dist.pip_install(["-r", "requirements.txt"]))

    return exe


def make_embedded_resources(exe):
    return exe.to_embedded_resources()


def make_install(exe):
    files = FileManifest()
    files.add_python_resource(".", exe)
    return files


# Enregistrement des cibles de build
register_target("exe", make_exe)
register_target("embedded_resources", make_embedded_resources, depends=["exe"])
register_target("install", make_install, depends=["exe"])

# Résolution globale des cibles
resolve_targets()
