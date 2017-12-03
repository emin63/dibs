This directory contains docker scripts and configuration information 
to setup our system.

# Windows Notes

On windows, you will probably want to do the following before you interact
with docker:

  1. Start a bash shell
  2. Do `eval "$(docker-machine env default)"` to setup the env.
  3. Do `docker-machine start default` to get the docker daemon working.

# Bringing machines up

After you have done the initial build, you can do something like

`   $ sudo docker-compose up`

to start the containers. 

## Be *CAREFUL* about docker-compose down

Be very *CAREFUL* about using a command like `docker-compose down`. It
will destory the existing containers. Probably you should just use
something like `docker exec -it dibs_main bash` to access a running machine.

If you really want to stop the whole docker-compose thing, use
something like `docker-compose stop` and then `docker-compose start`
so you don't destroy the containers.

