# Common Commands

Opening a shell to the notebooks image,

    docker-compose -f notebook.yml exec notebook /bin/bash

useful in case you want to run some commands affecting Jupyter
in some manner, or if you are trying to debug some Python-code
it can be convenient to open a Python-interpreter inside the
image as you can also readily access the file-system and
hopefully understand why some code is not working.
