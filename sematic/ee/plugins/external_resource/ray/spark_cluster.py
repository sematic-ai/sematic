from dataclasses import replace, dataclass
from subprocess import Popen
import os

# try:
#     import raydp
#     import pyspark
# except ImportError as e:
#     raise ImportError("To use RaySparkCluster you must depend on raydp and pyspark") from e

from sematic.ee.plugins.external_resource.ray.cluster import RayCluster


@dataclass(frozen=True)
class RaySparkCluster(RayCluster):
    
    def __post_init__(self):
        self._assert_java_installed()
    
    @classmethod
    def _init_spark(cls):
        _spark_home = os.environ.get("SPARK_HOME", os.path.dirname(pyspark.__file__))
        spark_jars_dir = os.path.abspath(os.path.join(_spark_home, "jars/*"))
        spark = raydp.init_spark(
            app_name = "example",
            num_executors = 2,
            executor_cores = 1,
            executor_memory = "2GB",
            configs={
                "raydp.executor.extraClassPath": spark_jars_dir,
            },
        )


    @classmethod
    def _assert_java_installed(cls):
        process = Popen(args=["java", "--version"])
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(
                "In order to use RaySparkCluster, you must have java installed"
            )