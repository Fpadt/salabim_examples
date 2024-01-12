# __init__.py
from . import subpackage

# This code will be executed when the package is imported.
print("Initializing package")

# Import specific modules when `from package import *` is used.
__all__ = ['subpackage']

# Import classes or functions into the package level so they can be used directly when importing the package.
# from .module1 import Class1
# from .module2 import function1