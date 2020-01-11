# Getting started
This file walks you through the setting up a development environment for synthbot. This means:
1. Setting up your directory structure,
2. Running the docker image, and
3. Running the dev environment.

## Setting up the directory structure
Step up your project directory:
```
mkdir soundtools # project directory to track relevant files
cd soundtools # we'll always assume we're working in this directory henceforth

mkdir data # keep data files organized in one place
git clone "https://github.com/synthbot-anon/synthbot.git"
```

The `data/` directory organization should reflect preprocessing flows. You'll be adding more directories in `data/` as you go through the preprocessing steps. For now, we'll just add two folders for Clipper's clips and our pronunciation dictionaries.
```
mkdir data/clipper-samples
mkdir data/dictionaries
```

Make sure you've downloaded and (if needed) extracted Clipper's Master File 2.0 into the `data/clipper-samples` directory. Make sure you've also downloaded `cmudict-0.7b.txt`, `librispeech.txt`, and `horsewords.txt`, and placed them within the `data/dictionaries` directory.

Within `soundtools/`, your directory structure should now look something like this:
```
data/
    clipper-samples/
        Reviewed episodes/
            # lots of .json files
            ...
        Sliced Dialogue/
            EQG/...
            FiM/...
            Label files/...
            ...
    dictionaries/
        cmudict-0.7b.txt
        librispeech.txt
        horsewords.txt
synthbot/
    notebooks/
    src/
    tests/
    requirements.txt
    ...
```

## Running the docker image
Make sure you've installed Docker. You can find the installation instructions [here](https://docs.docker.com/install/).

Once you've installed Docker, you can run the `soundtools` container with the following command:
```
docker run \
    --mount "type=bind,src=$(pwd)/data,dst=/home/celestia/data" \
    --mount "type=bind,src=$(pwd)/synthbot,dst=/home/celestia/synthbot" \
    --publish "127.0.0.1:8888:8888" \
    --publish "127.0.0.1:6006:6006" \
    --hostname "soundtools" \
    --rm -it synthbot/soundtools:latest
```

I recommend saving that as a shell script. You can add `--gpus 3` or similar to give the container access to your GPUs.

When you run the command, you should be dropped into an ubuntu 18.04 shell under the user `celestia`. Note that changes you make to container files WILL NOT persist when you exit the container. The only changes that persist will be ones performed on host files that are available within the container.

Walking through the `docker run` command line arguments:
* `--mount "type=bind,src=$(pwd)/data,dst=/home/celestia/data"` makes your `data/` directory available in the container using a bind mount. A bind mount is what's used to connect files across different partitions and filesystems on the same system. This is how we're making host files available within the container. Any changes you make within the `data/` directory inside the container will persist.
* `--mount "type=bind,src=$(pwd)/synthbot,dst=/home/celestia/synthbot"` makes your `synthbot/` directory available in the container, again using a bind mount. Any changes you make within the `synthbot/` directory will persist, and any change you make in the `synthbot/` directory on your host will be reflected back as changed within the container. This means you can use your IDE of choice outside of the container to modify code while running the actual code within the container, and you won't have to keep restarting the container to do this.
* `--publish "127.0.0.1:8888:8888"` forwards the container port 8888 to your host port 8888. The `127.0.0.1` forces this port to be available on your host computer in a way that it isn't exposed to the rest of the internet. This is good because we're eventually going to run Jupyter on this port, and anyone with access to this port will be able to execute arbitrary code within your container.
* `--publish "127.0.0.1:6006:6006"` forwards the necessary port for Tensorflow's TensorBoard.
* `--hostname "soundtools"` sets the network name of your container. This might have some utility later, but for now it just makes the command prompt less ugly.
* `--rm` tells Docker to clean up after itself once the container is done running. Don't remove this flag unless you know what you're doing, otherwise you'll find that Docker is consuming way more disk space than it seems to need.
* `-it synthbot/soundtools:latest` drops you into an interactive shell in the `synthbot/soundtools:latest` container hosted on [Docker Hub](https://hub.docker.com).

And you're set up! When the container starts, it will give you a `127.0.0.1:8888` URL you can open in your browser (outside of the container). The next step is to open the Jupyter URL in a browser, navigate to the `notebooks/` directory, and run through `Preprocess data.ipynb`. This will walk you through preprocessing the data.
