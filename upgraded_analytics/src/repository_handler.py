"""
Repository handling utilities for cloning and managing repositories.
"""

import os
import shutil
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)


class RepositoryHandler:
    """Handles repository cloning and cleanup operations."""
    
    def __init__(self, temp_base_dir: Optional[str] = None):
        """
        Initialize the repository handler.
        
        Args:
            temp_base_dir: Base directory for temporary repositories
        """
        self.temp_base_dir = temp_base_dir or tempfile.gettempdir()
        self.cloned_repos = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_all()
    
    def cleanup_all(self):
        """Clean up all cloned repositories."""
        for repo_path in self.cloned_repos:
            try:
                if os.path.exists(repo_path):
                    shutil.rmtree(repo_path)
                    logger.info(f"Cleaned up repository: {repo_path}")
            except Exception as e:
                logger.warning(f"Error cleaning up repository {repo_path}: {e}")
        self.cloned_repos.clear()
    
    def parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """
        Parse a repository URL to extract owner and repo name.
        
        Args:
            repo_url: Repository URL (e.g., 'owner/repo' or full GitHub URL)
            
        Returns:
            Tuple of (owner, repo_name)
            
        Raises:
            ValueError: If the URL format is invalid
        """
        # Handle different URL formats
        if repo_url.startswith('http'):
            # Full URL: https://github.com/owner/repo
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                return path_parts[0], path_parts[1].replace('.git', '')
            else:
                raise ValueError(f"Invalid GitHub URL format: {repo_url}")
        elif '/' in repo_url:
            # Short format: owner/repo
            parts = repo_url.split('/')
            if len(parts) == 2:
                return parts[0], parts[1]
            else:
                raise ValueError(f"Invalid repository format: {repo_url}")
        else:
            raise ValueError(f"Invalid repository format: {repo_url}")
    
    def get_github_repo_info(self, owner: str, repo_name: str) -> dict:
        """
        Get repository information from GitHub API.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            
        Returns:
            Repository information dictionary
        """
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching repository info for {owner}/{repo_name}: {e}")
            return {
                'description': 'No description available',
                'language': None,
                'size': 0,
                'stargazers_count': 0,
                'forks_count': 0,
                'open_issues_count': 0,
                'created_at': None,
                'updated_at': None,
                'pushed_at': None,
            }
    
    def clone_repository(self, repo_url: str, target_dir: Optional[str] = None) -> str:
        """
        Clone a repository to a local directory.
        
        Args:
            repo_url: Repository URL
            target_dir: Target directory (if None, creates a temporary directory)
            
        Returns:
            Path to the cloned repository
            
        Raises:
            subprocess.CalledProcessError: If git clone fails
        """
        owner, repo_name = self.parse_repo_url(repo_url)
        
        if target_dir is None:
            target_dir = tempfile.mkdtemp(
                prefix=f"{owner}_{repo_name}_",
                dir=self.temp_base_dir
            )
        
        # Construct the full GitHub URL
        if not repo_url.startswith('http'):
            clone_url = f"https://github.com/{owner}/{repo_name}.git"
        else:
            clone_url = repo_url
            if not clone_url.endswith('.git'):
                clone_url += '.git'
        
        logger.info(f"Cloning repository {clone_url} to {target_dir}")
        
        try:
            # Clone with depth=1 for faster cloning (shallow clone)
            subprocess.run([
                'git', 'clone', '--depth', '1', clone_url, target_dir
            ], check=True, capture_output=True, text=True)
            
            self.cloned_repos.append(target_dir)
            logger.info(f"Successfully cloned repository to {target_dir}")
            return target_dir
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository {clone_url}: {e.stderr}")
            # Clean up failed clone directory
            if os.path.exists(target_dir):
                try:
                    shutil.rmtree(target_dir)
                except Exception:
                    pass
            raise
    
    def get_monthly_commits(self, repo_path: str, owner: str, repo_name: str) -> dict:
        """
        Get monthly commit counts for the repository.
        
        Args:
            repo_path: Path to the cloned repository
            owner: Repository owner
            repo_name: Repository name
            
        Returns:
            Dictionary with month-year keys and commit counts
        """
        try:
            # Change to repository directory
            original_dir = os.getcwd()
            os.chdir(repo_path)
            
            # Get commits from the last 12 months
            cmd = [
                'git', 'log',
                '--since=12 months ago',
                '--format=%aI'  # ISO 8601 format
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commit_dates = result.stdout.strip().split('\n')
            
            # Count commits by month
            monthly_counts = {}
            for date_str in commit_dates:
                if date_str:  # Skip empty lines
                    try:
                        # Extract year-month from ISO date
                        month_key = date_str[:7]  # YYYY-MM
                        monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
                    except Exception:
                        continue
            
            # Fill in missing months with 0
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                month_key = current_date.strftime('%Y-%m')
                if month_key not in monthly_counts:
                    monthly_counts[month_key] = 0
                current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            
            os.chdir(original_dir)
            return dict(sorted(monthly_counts.items()))
            
        except Exception as e:
            logger.error(f"Error getting monthly commits for {owner}/{repo_name}: {e}")
            try:
                os.chdir(original_dir)
            except:
                pass
            return {}
    
    def get_repository_stats(self, repo_path: str) -> dict:
        """
        Get basic statistics about the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary with repository statistics
        """
        stats = {
            'total_files': 0,
            'total_size_bytes': 0,
            'file_types': {},
            'directory_count': 0,
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                stats['directory_count'] += len(dirs)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        stats['total_files'] += 1
                        stats['total_size_bytes'] += file_size
                        
                        # Count file types
                        ext = Path(file).suffix.lower()
                        if ext:
                            stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                        else:
                            stats['file_types']['no_extension'] = stats['file_types'].get('no_extension', 0) + 1
                    except OSError:
                        continue
        
        except Exception as e:
            logger.error(f"Error getting repository stats for {repo_path}: {e}")
        
        return stats

