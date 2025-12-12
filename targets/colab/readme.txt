As of right now, you can train in three ways.  

Desktop
From the a linux desktop with a GPU, such as the A4500 and using either
the docker image in the targets/nvidia folder, or with a python environment file created from requirements.txt.  

Colab
Just load the jupyter notbook into colab and follow it

Nvidia Tegra (Orin AGX)
A Nano is too small. An AGX will train about as fast as a colab T4.  You need to start the container 
in the targets/nvidia folder, and then you can run the jupyter notebook in a vscode environment
connected to the container


Future mod maybe - run from pythong environment on the Nvidia Tegra
Currently, ultralytics installs torchvision without gpu support on tegra, so you need to reinstall it per the following:

https://docs.ultralytics.com/guides/nvidia-jetson/#install-pytorch-and-torchvision_1

pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torch-2.5.0a0+872d972e41.nv24.08-cp310-cp310-linux_aarch64.whl
pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl

As of right now, I did not want to complicate matters by having a special build script just to enable training from an nvidia
python environment when the same is already in place bgy the docker method already described.
