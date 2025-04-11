__version__ = "0.0.1" # Initial version of CLI tool for SQL Agent Tool, overall versioning is managed in the main package
from .cli import load_config, init, query, shell, update
__all__ = ["load_config", "init", "query", "shell", "update"]
__author__ = "Harsh Dadiya"
__email__ = "harshdadiya@gmail.com"
__license__ = "MIT"
__copyright__ = "2025 Harsh Dadiya"

__status__ = "Development" # Development status of the project
__maintainer__ = "Harsh Dadiya"
__credits__ = ["Harsh Dadiya"]
# End of metadata