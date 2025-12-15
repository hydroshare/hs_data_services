# HydroShare Data Services 1.0.0
# Django 3.0.1


FROM ubuntu:18.04


MAINTAINER Kenneth Lippold kjlippold@gmail.com


# Apt Setup ----------------------------------------------------------------------------------------------#

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install wget vim sudo supervisor -y


# Create dsuser user --------------------------------------------------------------------------------------#

RUN adduser --disabled-password --gecos '' dsuser
RUN adduser dsuser sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER dsuser

ENV DS_HOME /home/dsuser
WORKDIR $DS_HOME
RUN chmod a+rwx $DS_HOME

# Setup Mamba Environment --------------------------------------------------------------------------------#

# Install Miniforge/Mamba for dsuser
RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" \
  && chmod +x Miniforge3-$(uname)-$(uname -m).sh \
  && bash Miniforge3-$(uname)-$(uname -m).sh -b \
  && rm Miniforge3-$(uname)-$(uname -m).sh

# Update PATH for dsuser
ENV PATH="/home/dsuser/miniforge3/bin:${PATH}"

RUN mamba install -y \
  --channel conda-forge \
  --channel anaconda \
  ipyleaflet \
  nbconvert \
  nbformat \
  jupyter_client \
  ipympl \
  pyopenssl \
  && mamba clean --all -f -y

COPY hs_data_services/environment.yml $DS_HOME/hs_data_services/environment.yml
RUN sudo chown -R dsuser $DS_HOME/hs_data_services
RUN conda env create -f $DS_HOME/hs_data_services/environment.yml


# Place Application Files --------------------------------------------------------------------------------#

COPY hs_data_services/ $DS_HOME/hs_data_services
COPY conf/ $DS_HOME/conf

RUN sudo chmod -R +x $DS_HOME/conf
RUN sudo chown -R dsuser $DS_HOME/hs_data_services
RUN sudo chown -R dsuser $DS_HOME/conf


# Activate Conda Environment -----------------------------------------------------------------------------#

RUN echo "source activate hs_data_services" > ~/.bashrc