import os, sys

_viewers = []
def register(viewer, order=1):
    try:
        if issubclass(viewer, Viewer):
            viewer = viewer()
    except TypeError:
        pass # raised if viewer wasn't a class
    if order > 0:
        _viewers.append(viewer)
    elif order < 0:
        _viewers.insert(0, viewer)

##
# Displays a given image.
#
# @param title Optional title.  Not all viewers can display the title.
# @param **options Additional viewer options.
# @return True if a suitable viewer was found, false otherwise.

def show(image, title=None, **options):
    for viewer in _viewers:
        if viewer.show(image, title=title, **options):
            return 1
    return 0

##
# Base class for viewers.

class Viewer:

    # main api

    def show(self, image, **options):

        self.show_file(image, **options)

    # hook methods

    def get_command(self, file, **options):
        raise NotImplementedError

    def show_file(self, file, **options):
        # display given file
        os.system(self.get_command(file, **options))
        return 1

# --------------------------------------------------------------------

if sys.platform == "win32":

    class WindowsViewer(Viewer):
        def get_command(self, file, **options):
            return "%s&" % file

    register(WindowsViewer)

elif sys.platform == "darwin":

    class MacViewer(Viewer):
        def get_command(self, file, **options):
            # on darwin open returns immediately resulting in the temp
            # file removal while app is opening
            command = "open -a /Applications/Preview.app"
            command = "(%s %s;)&" % (command, file)
            return command

    register(MacViewer)

else:

    # unixoids

    def which(executable):
        path = os.environ.get("PATH")
        if not path:
            return None
        for dirname in path.split(os.pathsep):
            filename = os.path.join(dirname, executable)
            if os.path.isfile(filename):
                # FIXME: make sure it's executable
                return filename
        return None

    class UnixViewer(Viewer):
        def show_file(self, file, **options):
            command, executable = self.get_command_ex(file, **options)
            command = "(%s %s;)&" % (command,file)
            os.system(command)
            return 1

    # implementations

    class DisplayViewer(UnixViewer):
        def get_command_ex(self, file, **options):
            command = executable = "display"
            return command, executable

    if which("display"):
        register(DisplayViewer)

    class XVViewer(UnixViewer):
        def get_command_ex(self, file, title=None, **options):
            # note: xv is pretty outdated.  most modern systems have
            # imagemagick's display command instead.
            command = executable = "xv"
            if title:
                # FIXME: do full escaping
                command = command + " -name \"%s\"" % title
            return command, executable

    if which("xv"):
        register(XVViewer)

if __name__ == "__main__":
    # usage: python ImageShow.py imagefile [title]
    print show(sys.argv[1], *sys.argv[2:])
