# Getting started
This file walks you through the setting up a development environment for synthbot. This means:
1. Setting up your directory structure,
2. Running the docker image,
3. Running the dev environment, and
4. Best practices I've found.

## Setting up the directory structure
Step up your project directory:
```
mkdir soundtools # project directory to track relevant files
cd soundtools # we'll always assume we're working in this directory henceforth

mkdir data # keep data files organized in one place
git clone `synthbot repo goes here`
```

The `data/` directory organization should reflect preprocessing flows. You'll be adding more directories in `data/` as you go through the preprocessing steps. For now, we'll just add a folder for Clipper's clips.
```
mkdir data/clipper-samples
```

Make sure you've downloaded and (if needed) extracted Clipper's files into the `data/clipper-samples` directory. Within `soundtools/`, your directory structure should now look something like this:
```
data/
    clipper-samples/
        S1/
            s1e1/
                # lots of .flac and .txt files
            s1e2/
                # lots of .flac and .txt files
            ...
        S2/
            ...
        ...
synthbot/
    notebooks/
    src/
    tests/
    Pipfile
    Pipfile.lock
    ...
```

## Running the docker image
Make sure you've installed Docker. You can find the installation instructions [here](https://docs.docker.com/install/). If you have an nvidia graphics card with cuda support, I recommend also getting the [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker) so you can use gpu acceleration later on, though you can install this later.

Once you've installed Docker, you can run the synthbot container with the following command:
```
docker run \
    --mount "type=bind,src=$(pwd)/data,dst=/home/celestia/data" \
    --mount "type=bind,src=$(pwd)/synthbot,dst=/home/celestia/synthbot" \
    --publish "127.0.0.1:8888:8888" \
    --hostname "synthbot" \
    --rm -it sunnysd/synthbot:lastest
```

I recommend saving that as a shell script.

When you run the command, you should be dropped into an ubuntu 18.04 shell under the user `celestia`. Note that changes you make to container files WILL NOT persist when you exit the container. The only changes that persist will be ones performed on host files that are available within the container.

Walking through the `docker run` command line arguments:
* `--mount "type=bind,src=$(pwd)/data,dst=/home/celestia/data"` makes your `data/` directory available in the container using a bind mount. A bind mount is what's used to connect files across different partitions and filesystems on the same system. This is how we're making host files available within the container. Any changes you make within the `data/` directory inside the container will persist.
* `--mount "type=bind,src=$(pwd)/synthbot,dst=/home/celestia/synthbot"` makes your `synthbot/` directory available in the container, again using a bind mount. Any changes you make within the `synthbot/` directory will persist, and any change you make in the `synthbot/` directory on your host will be reflected back as changed within the container. This means you can use your IDE of choice outside of the container to modify code while running the actual code within the container, and you won't have to keep restarting the container to do this.
* `--publish "127.0.0.1:8888:8888"` forwards the container port 8888 to your host port 8888. The `127.0.0.1` forces this port to be available on your host computer in a way that it isn't exposed to the rest of the internet. This is good because we're eventually going to run Jupyter on this port, and anyone with access to this port will be able to execute arbitrary code within your container.
* `--hostname "soundtools"` sets the network name of your container. This might have some utility later, but for now it just makes the command prompt less ugly.
* `--rm` tells Docker to clean up after itself once the container is done running. Don't remove this flag unless you know what you're doing, otherwise you'll find that Docker is consuming way more disk space than it seems to need.
* `-it sunnysd/synthbot:lastest` drops you into an interactive shell in the `sunnysd/synthbot:latest` container hosted on [Docker Hub](https://hub.docker.com).

## Running the dev environment
Inside the container, you can set up the development environment with:
```
cd synthbot
pipenv install --dev
pipenv shell
```

Pipenv is a package management tool for dealing with python packages. In general, I install packages through `pipenv install` whenever possible, and I add them to the Docker container whenever not. Later on, if I ever get to hosting this on [PyPI](https://pypi.org), I expect this will simplify installation.

The above commands install the packages and tools needed to develop against synthbot, then drop you into a shell in which the packages are available. You can see which packages get installed by reading through `Pipfile`.

Once in the pipenv shell, you can run jupyter and start going through the available `notebooks/`.
```
jupyter notebook --ip 0.0.0.0 --no-browser
```

An explanation of the arguments:
* `--ip 0.0.0.0` tells Jupyter to listen for connections from all interfaces. These are interfaces within the Docker container. People can't connect from the open internet. With our earlier `--publish` argument passed to `docker run`, you'll be able to connect from your host machine.
* `--no-browser` tells Jupyter not to open a browser to the notebook. You can try to get a browser working in the container, but you'll probably run into sound and graphics issues since it can get complicated trying to share devices with two operating systems. Jupyter drastically simplifies the process of playing back sound from a Python interpreter, which will be useful during development.

And you're set up! The `jupyter` command will give you a `127.0.0.1:8888` URL you can open in your browser (outside of the container). You have two next steps:
* Open the Jupyter URL in a browser, navigate to the `notebooks/` directory, and run through `2. Preprocess data.ipynb`. This will walk you through preprocessing the data.
* Then run through `notebooks/3. Hello world.ipynb` to see how to access the resulting data.

## Best practices
