"""Auto-discovery fallback for APIRouter instances.

This module provides a safe fallback mechanism to discover and register
any APIRouter instances that weren't explicitly included in main.py.
It walks the app directory tree and attempts to import modules that
might contain routers, logging warnings for any issues but never
crashing the application startup.
"""

import importlib
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger("ziggy.router_auto")


def discover_and_register_routers(app: "FastAPI") -> None:
    """Discover and register any APIRouter instances not already included.

    Args:
        app: The FastAPI application instance

    This function:
    - Walks the app directory tree (skipping tests, __pycache__, migrations)
    - Imports modules with try/except logging only (no crashes)
    - Registers any global APIRouter not already included
    - Honors ROUTER_PREFIX if present; avoids double slashes
    """
    # Get the app directory path
    app_dir = Path(__file__).parent.parent

    # Track already registered routers by their object id to avoid duplicates
    registered_router_ids = set()
    for route in app.routes:
        # If the route has a parent router, track its id
        if hasattr(route, "dependant") and hasattr(route.dependant, "path_operation"):
            router_ref = getattr(route.dependant.path_operation, "router", None)
            if router_ref:
                registered_router_ids.add(id(router_ref))

    # Also track route paths to detect duplicates
    registered_paths = set()
    for route in app.routes:
        if hasattr(route, "path"):
            registered_paths.add(route.path)

    logger.info(f"Auto-discovery starting with {len(registered_paths)} existing routes")

    # Directories to skip
    skip_dirs = {"__pycache__", "tests", "test", "migrations", ".pytest_cache"}

    # Walk the app directory
    for root, dirs, files in os.walk(app_dir):
        # Filter out skip directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if not file.endswith(".py") or file.startswith("_"):
                continue

            # Build module path
            file_path = Path(root) / file
            try:
                rel_path = file_path.relative_to(app_dir.parent)
                module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")

                # Try to import the module
                try:
                    module = importlib.import_module(module_path)
                except Exception as e:
                    logger.debug(f"Could not import {module_path}: {e}")
                    continue

                # Look for 'router' attribute
                if not hasattr(module, "router"):
                    continue

                router = getattr(module, "router")

                # Check if this router is already registered by object id
                router_id = id(router)
                if router_id in registered_router_ids:
                    logger.debug(
                        f"Router from {module_path} already registered (by id), skipping"
                    )
                    continue

                # Check if this looks like an APIRouter
                if not hasattr(router, "routes"):
                    continue

                # Check if any routes from this router are already registered
                router_routes = getattr(router, "routes", [])
                if not router_routes:
                    continue

                # Check for overlap with existing routes by checking multiple routes
                overlapping_routes = 0
                for route in router_routes:
                    if hasattr(route, "path"):
                        route_path = getattr(route, "path", "")
                        # Check both with and without potential prefixes
                        for prefix_test in ["", "/api", "/web"]:
                            test_path = prefix_test + route_path
                            if test_path in registered_paths:
                                overlapping_routes += 1
                                break

                # If more than half the routes overlap, consider this router already registered
                if overlapping_routes > len(router_routes) / 2:
                    logger.debug(
                        f"Router from {module_path} mostly registered "
                        f"({overlapping_routes}/{len(router_routes)} routes), skipping"
                    )
                    continue

                # Check for ROUTER_PREFIX in the module
                prefix = getattr(module, "ROUTER_PREFIX", None)
                if prefix is None:
                    # Check if router already has a prefix
                    prefix = getattr(router, "prefix", "")

                # Ensure single leading slash, no trailing slash
                if prefix:
                    prefix = "/" + prefix.strip("/")

                # Register the router
                try:
                    if prefix:
                        app.include_router(router, prefix=prefix)
                        logger.info(
                            f"Auto-registered router from {module_path} with prefix {prefix}"
                        )
                    else:
                        app.include_router(router)
                        logger.info(
                            f"Auto-registered router from {module_path} (no prefix)"
                        )

                    # Track this router and its paths
                    registered_router_ids.add(router_id)
                    for route in router_routes:
                        if hasattr(route, "path"):
                            full_path = prefix + getattr(route, "path", "")
                            registered_paths.add(full_path)

                except Exception as e:
                    logger.warning(f"Failed to register router from {module_path}: {e}")

            except Exception as e:
                logger.debug(f"Error processing {file_path}: {e}")

    logger.info(f"Auto-discovery complete, total routes: {len(app.routes)}")
