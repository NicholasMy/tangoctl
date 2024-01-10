# Create tangoctl_installed.py with a calculated path to the virtualenv
echo "#!${PWD}/venv/bin/python3
import os
import tangoctl
if __name__ == '__main__':
    os.chdir('${PWD}')
    tangoctl.main()" > tangoctl_installed.py

# Make both scripts executable
chmod 755 tangoctl_installed.py tangoctl.py

# Create a symlink to tangoctl_installed.py so that `tangoctl` can be run from anywhere
ln -s "${PWD}/tangoctl_installed.py" /usr/local/bin/tangoctl