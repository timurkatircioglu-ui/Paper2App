"""Schema-driven runtime package for Paper2App.

W01 intentionally keeps package initialization side-effect free because the
AppSpec validator derives its default capability profile from runtime.manifest.
Import concrete runtime contracts from paper2app.runtime.manifest or
paper2app.runtime.registry.
"""
