# What's going on in this file?
###############################
#
# Ok, so Sematic depends on some libraries that support a wide range
# of python versions. Some of these may support python before the
# typing module was officially in the stdlib, but still want to make
# use of typing. Luckily, for such users there is this backport:
# https://pypi.org/project/typing/
# One example of a lib that uses this is raydp.
#
# The downside of depending on libs that depend on the typing
# backport is that we then have a transitive dependency on it.
# This *shouldn't* be a big deal--ideally the built-in typing
# library should be found before the third-party backport is.
#
# ...Unfortunately that's not what happens in bazel (by default).
# And when the backport "typing" is found in a newer python version,
# other standard lib stuff that depend on things in their co-bundled
# version of "typing" break. Ex:
# https://stackoverflow.com/questions/75262818/avoid-transitive-dependency-on-python-typing-backport
# This should raise a couple of questions:
# (1) Can we fix it for bazel?
# (2) Will end-users hit this?
#
# This file exists to address (1). Here's how it works:
# Python has some things it does before it begins executing the file/module
# you launched it to execute. Most of these things have to do with
# prepping to do imports in the main body of the execution.
# Details can be found here:
# https://docs.python.org/3/library/site.html
# You can customize how some of this behavior works, by including a
# sitecustomize.py file somewhere on the bootstrapped python
# path. This is such a file. It is saying "if there's something
# on the sys.path that looks like the typing BACKPORT, then
# remove it from the sys.path." This makes it so the backport is
# not found, and instead the one bundled with the python release
# is found.
#
# But what about question (2)? Will end users have to worry about this?
# If they are using bazel, then...yes. But this would be true if
# they depended on ANY lib that depended transitively on "typing,"
# so Sematic is not really making the world much worse. We should document
# this solution, and guide our bazel users to it.
#
# What about non-bazel users? They should most likely not run into it.
# How do we know this? The answer requires a bit of explanation:
# For *certain* built-ins, python does not use the sys.path
# at all to look them up, but rather first uses a special importer,
# importlib.machinery.BuiltinImporter
# https://docs.python.org/3/library/importlib.html#importlib.machinery.BuiltinImporter
# Only later is the path importer (importlib.machinery.PathFinder) used.
# The keyword there is *certain* built-ins, and "typing" does not
# appear to be among them. Even when looking up the standard library
# typing, it goes through the PathFinder.
# However, *usually* your sys.path should contain the root dir of your python
# install near the front of the path. However, bazel does not
# set up the path in this way, instead sometimes putting
# pip dependency directories on the path first. This is really probably
# a bug in bazel or rules_python, but since it's not fixed
# as of 1/31/2023, we may need to live with it for a while.
#
# Addendum: if your terminal has a virtualenv activated, you may
# still see some errors like this:
# AttributeError: type object 'Callable' has no attribute '_abc_registry'
# BEFORE your application (test, main file, etc) actually starts.
# If so, they can be safely ignored. As far as I can tell, these
# are coming from when bazel is bootstrapping its python env
# (see stub.py.tpl) from the currently active interprerter.
# The errors will all be from `.pth` files in your virtual env,
# which are special import actions being set up by those libs
# before the main interpreter work begins.


import sys
if "typing" in sys.modules:
    del sys.modules["typing"]

def is_typing_backport(path):
    segments = path.split("/")
    return any("typing" in segment and "pip" in segment for segment in segments)

sys.path = [pth for pth in sys.path if not is_typing_backport(pth)]