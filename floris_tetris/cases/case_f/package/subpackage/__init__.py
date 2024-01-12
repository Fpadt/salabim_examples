# __init__.py
from . import child

# This code will be executed when the package is imported.
print("Initializing subpackage")

# Import specific modules when `from package import *` is used.
__all__ = ['child']

# Import classes or functions into the package level so they can be used directly when importing the package.
# from .module1 import Class1
# from .module2 import function1