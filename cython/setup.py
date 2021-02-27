from setuptools import setup
from Cython.Build import cythonize
from Cython.Compiler import Options

Options.embed = True
Options.embed = "knots"

setup(
    name='knots',
    ext_modules=cythonize(["*.pyx", "./knot_modules/*.pyx"], compiler_directives={'language_level': "3"}),
)
