# Deployment	
Notes for developers about to deploy the code.

## Tox
Run `tox` to ensure all tests pass.

Tox will automatically build the files to post to pypi, including a `.whl` and a `tar.gz` file.

## Post to PyPI

`twine upload dist/*`
