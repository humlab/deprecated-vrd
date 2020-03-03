# Common Commands

Opening a shell to the notebooks image,

    docker-compose -f notebook.yml exec notebook /bin/bash

useful in case you want to run some commands affecting Jupyter
in some manner, or if you are trying to debug some Python-code
it can be convenient to open a Python-interpreter inside the
image as you can also readily access the file-system and
hopefully understand why some code is not working.

## Tests

To run a single API-test, one example would be

    docker-compose exec middleware python -m unittest middleware.tests.functional.test_files_api.FilesRoutesTest.test_file_info_route_for_file_that_does_not_exist

## Database

To open a Flask Shell

    docker-compose exec -e FLASK_APP=middleware/__init__.py middleware flask shell
