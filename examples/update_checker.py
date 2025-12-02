"""
Blood on the Clocktower Data Update Checker

Example code showing how to can check for and download
updates from the GitHub releases.

Usage:
    # Check if update is available
    python update_checker.py --check
    
    # Download latest release
    python update_checker.py --download
    
    # Download to specific directory
    python update_checker.py --download --output ./data

This example demonstrates the update flow:
1. Fetch manifest.json from latest GitHub release
2. Compare local version with remote version
3. If newer, download and extract the full package
"""

import json
import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("This example requires the 'requests' library.")
    print("Install with: pip install requests")
    exit(1)

# GitHub repository info
GITHUB_OWNER = "Phauks"
GITHUB_REPO = "Blood-on-the-Clocktower---Official-Data-Sync"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Raw content URL for manifest (can fetch without downloading full release)
RAW_MANIFEST_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/dist/manifest.json"


def get_local_manifest(data_dir: Path) -> Optional[dict]:
    """Load local manifest.json if it exists.
    
    Args:
        data_dir: Directory containing local data
    
    Returns:
        Manifest dict or None if not found
    """
    manifest_path = data_dir / "manifest.json"
    
    if not manifest_path.exists():
        return None
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_remote_manifest() -> Optional[dict]:
    """Fetch the latest manifest from GitHub.
    
    First tries the raw manifest URL (faster), falls back to release API.
    
    Returns:
        Manifest dict or None if fetch failed
    """
    # Try raw manifest first (faster, no API rate limits)
    try:
        response = requests.get(RAW_MANIFEST_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
    except (requests.RequestException, json.JSONDecodeError):
        pass
    
    # Fall back to release API
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        if response.status_code != 200:
            return None
        
        release = response.json()
        
        # Find manifest.json in release assets
        for asset in release.get("assets", []):
            if asset["name"] == "manifest.json":
                manifest_response = requests.get(asset["browser_download_url"], timeout=10)
                if manifest_response.status_code == 200:
                    return manifest_response.json()
        
        return None
        
    except (requests.RequestException, json.JSONDecodeError):
        return None


def check_for_update(data_dir: Path) -> dict:
    """Check if an update is available.
    
    Args:
        data_dir: Directory containing local data
    
    Returns:
        Dict with update status:
        {
            "update_available": bool,
            "local_version": str or None,
            "remote_version": str or None,
            "local_hash": str or None,
            "remote_hash": str or None,
        }
    """
    result = {
        "update_available": False,
        "local_version": None,
        "remote_version": None,
        "local_hash": None,
        "remote_hash": None,
    }
    
    local = get_local_manifest(data_dir)
    remote = get_remote_manifest()
    
    if local:
        result["local_version"] = local.get("version")
        result["local_hash"] = local.get("contentHash")
    
    if remote:
        result["remote_version"] = remote.get("version")
        result["remote_hash"] = remote.get("contentHash")
    
    # Determine if update is needed
    if not local:
        # No local data - need to download
        result["update_available"] = remote is not None
    elif not remote:
        # Can't reach remote - no update
        result["update_available"] = False
    else:
        # Compare content hashes (most reliable) or versions
        if result["local_hash"] and result["remote_hash"]:
            result["update_available"] = result["local_hash"] != result["remote_hash"]
        else:
            # Fall back to version comparison
            result["update_available"] = result["local_version"] != result["remote_version"]
    
    return result


def get_latest_release_info() -> Optional[dict]:
    """Get information about the latest GitHub release.
    
    Returns:
        Release info dict or None if fetch failed
    """
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        if response.status_code != 200:
            return None
        return response.json()
    except requests.RequestException:
        return None


def download_latest_release(output_dir: Path, verbose: bool = True) -> bool:
    """Download and extract the latest release.
    
    Args:
        output_dir: Directory to extract files to
        verbose: Print progress
    
    Returns:
        True if download was successful
    """
    if verbose:
        print("Fetching latest release info...")
    
    release = get_latest_release_info()
    if not release:
        if verbose:
            print("Error: Could not fetch release info")
        return False
    
    # Find the ZIP asset
    zip_asset = None
    for asset in release.get("assets", []):
        if asset["name"].endswith(".zip"):
            zip_asset = asset
            break
    
    if not zip_asset:
        if verbose:
            print("Error: No ZIP file found in release assets")
        return False
    
    download_url = zip_asset["browser_download_url"]
    file_size = zip_asset.get("size", 0)
    
    if verbose:
        size_mb = file_size / (1024 * 1024)
        print(f"Downloading {zip_asset['name']} ({size_mb:.1f} MB)...")
    
    try:
        response = requests.get(download_url, timeout=60, stream=True)
        if response.status_code != 200:
            if verbose:
                print(f"Error: Download failed with status {response.status_code}")
            return False
        
        # Read ZIP into memory
        zip_data = BytesIO(response.content)
        
        if verbose:
            print("Extracting files...")
        
        # Extract to output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_data, "r") as zf:
            zf.extractall(output_dir)
        
        if verbose:
            print(f"Extracted to {output_dir}")
        
        return True
        
    except (requests.RequestException, zipfile.BadZipFile) as e:
        if verbose:
            print(f"Error: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check for and download Blood on the Clocktower data updates"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if an update is available"
    )
    
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the latest release"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./botc-data"),
        help="Output directory for downloaded data (default: ./botc-data)"
    )
    
    args = parser.parse_args()
    
    if not args.check and not args.download:
        parser.print_help()
        return
    
    if args.check:
        print("Checking for updates...")
        status = check_for_update(args.output)
        
        print(f"\nLocal version:  {status['local_version'] or 'Not installed'}")
        print(f"Remote version: {status['remote_version'] or 'Unknown'}")
        
        if status["update_available"]:
            print("\n✓ Update available!")
            if status["local_hash"] and status["remote_hash"]:
                print(f"  Hash changed: {status['local_hash']} → {status['remote_hash']}")
        else:
            print("\n✓ You have the latest version")
    
    if args.download:
        success = download_latest_release(args.output, verbose=True)
        if success:
            print("\n✓ Download complete!")
        else:
            print("\n✗ Download failed")
            exit(1)


if __name__ == "__main__":
    main()
