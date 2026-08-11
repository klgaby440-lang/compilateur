from setuptools import setup, Extension
from Cython.Build import cythonize
import os

# 1. Liste des fichiers cibles prioritaires pour SokoMaster
candidats = ["securite.py", "base_donnees.py", "main.py"]

# 2. On ne garde que les fichiers qui existent réellement sur le disque
modules_a_compiler = [f for f in candidats if os.path.exists(f)]

# 3. Si aucun fichier prioritaire n'est trouve, on compile les fichiers .py de la racine
if not modules_a_compiler:
    modules_a_compiler = [
        f for f in os.listdir('.') 
        if f.endswith('.py') and f != 'setup.py'
    ]

# 4. Lancement de la compilation Cython si des fichiers existent
if modules_a_compiler:
    print(f"Modules trouves pour la compilation Cython : {modules_a_compiler}")
    setup(
        name="SokoMaster Core Native",
        version="1.4.2",
        description="Module native compile Cython pour SokoMaster",
        author="CRYPT Enterprise",
        ext_modules=cythonize(
            modules_a_compiler,
            compiler_directives={
                'language_level': "3",
                'always_allow_keywords': True,
                'embedsignature': True
            }
        )
    )
else:
    print("Avertissement : Aucun fichier Python valide a compiler n'a ete trouve.")
