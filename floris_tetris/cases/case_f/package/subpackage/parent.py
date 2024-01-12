from .child import _child_function

def parent_function():
    print("This is the parent function.")
    print(f"Executed by parent {_child_function()}")