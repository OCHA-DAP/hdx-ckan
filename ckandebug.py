import ckan
import ckan.cli.cli

if __name__ == "__main__":
    """
    Run CKAN CLI without installing CKAN as package.
    Useful for development and debugging purposes.
    Example:
      $ python3 -m ckandebug -c test-core.ini run --host 0.0.0.0
    """
    ckan.cli.cli.ckan()
