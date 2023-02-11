# Each key in this dict will add a new "extra" that 
# can be installed with Sematic. Ex: the "ray" entry
# allows `pip install sematic[ray]`. There will also
# be an "all" entry added that allows installing all
# extras. Ex: `pip install sematic[all]` will install
# the ray extra and any others.
EXTRAS = {
    "ray": dict(
        sematic_module="//sematic/ee:ray",
        requires=["ray[default]>=2.1.0"]
    ),
}

EXTRA_SEMATIC_DEPS = [value["sematic_module"] for value in EXTRAS.values()]
EXTRA_REQUIRES = {key: value["requires"] for key, value in EXTRAS.items()}

def _get_all_extra_requires():
    all_extra_requires = []
    for value in EXTRAS.values():
        all_extra_requires.extend(value["requires"])
    return all_extra_requires

EXTRA_REQUIRES["all"] = _get_all_extra_requires()