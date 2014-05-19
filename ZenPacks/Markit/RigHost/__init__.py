import Globals

from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import unused, zenPath

import os

unused(Globals)
_plugins = [
    'rig_host_app_transform1.py',
    'copy_server_config_file.sh',
    ]


class ZenPack(ZenPackBase):

    def install(self, app):
        super(ZenPack, self).install(app)
        self.symlink_plugins()

    def symlink_plugins(self):
        libexec = os.path.join(os.environ.get('ZENHOME'), 'libexec')
        if not os.path.isdir(libexec):
            # Stack installs might not have a \$ZENHOME/libexec directory.
            os.mkdir(libexec)

        # Now get the path to the file in the ZenPack's libexec directory
        filepath = __file__ # Get path to this file
        (zpdir, tail) = os.path.split(filepath)
        zp_libexec_dir = os.path.join(zpdir,'libexec')
        for plugin in _plugins:
            plugin_path = zenPath('libexec', plugin)
            zp_plugin_path = os.path.join(zp_libexec_dir, plugin)
            #os.system('ln -sf "%s" "%s"' % (self.path(plugin), plugin_path))
            os.system('ln -sf "%s" "%s"' % (zp_plugin_path, plugin_path))
            os.system('chmod 0755 %s' % plugin_path)

    def remove_plugin_symlinks(self):
        for plugin in _plugins:
            os.system('rm -f "%s"' % zenPath('libexec', plugin))

    def remove(self, app, leaveObjects=False):
        if not leaveObjects:
            self.remove_plugin_symlinks()
        super(ZenPack, self).remove(app, leaveObjects=leaveObjects)

