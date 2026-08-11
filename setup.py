from setuptools import setup, Extension
from Cython.Build import cythonize
import os

# Liste uniquement tes modules cœurs stratégiques (Sécurité, BDD, etc.)
modules_a_compiler = [
    "securite.py",
    "base_donnees.py"
]

setup(
    name="SokoMaster Core Native",
    version="1.4.2",
    description="Module natif compilé Cython pour l'écosystème SokoMaster",
    author="CRYPT Enterprise",
    ext_modules=cythonize(
        modules_a_compiler,
        compiler_directives={
            'language_level': "3",              # Force l'analyseur en Python 3
            'always_allow_keywords': True,       # Conserve le support complet des arguments nommés
            'embedsignature': True              # Intègre les signatures de fonctions pour un débogage propre
        }
    )
)
