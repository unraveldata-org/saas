# Python standard library imports

# Third-party imports

# Local imports (which should try to avoid in this file)

class CLUSTER_TYPE:
    # HDI has Hadoop, HBase, Kafka, Interactive, Spark, and Storm
    # EMR has no such concept since allows cherry-picking.
    HADOOP = "HADOOP"
    HBASE = "HBASE"
    KAFKA = "KAFKA"
    INTERACTIVE_QUERY = "INTERACTIVE_QUERY"
    SPARK = "SPARK"
    STORM = "STORM"

    # Default used by that specific cloud provider
    DEFAULT = "DEFAULT"

    ALL = [HADOOP, HBASE, KAFKA, INTERACTIVE_QUERY, SPARK, STORM, DEFAULT]


class STACK_VERSION:
    """
    The ClusterSpecModel can specify which stack version to use, as either LATEST, STABLE, or an actual number
    which then gets translated into SPECIFIC.
    """
    LATEST = "LATEST"
    STABLE = "STABLE"
    SPECIFIC = "SPECIFIC"


class MARKET_TYPE:
    """
    How to bid and provision resources. Typically, we always use ON_DEMAND.
    Each Cloud Provider will be responsible for doing a mapping to its internal names.
    """
    ON_DEMAND = "ON_DEMAND"
    SPOT = "SPOT"


class SERVICE:
    """
    Contains the union of all services that we care about across all Cloud Providers.
    Each Cloud Provider will be responsible for doing a mapping to its internal names.
    """

    AIRFLOW = "Airflow"
    AMBARI = "Ambari"
    HADOOP = "Hadoop"
    GANGLIA = "Ganglia"
    HBASE = "HBase"
    HCATALOG = "HCatalog"
    HIVE = "Hive"
    HUE = "Hue"
    IMPALA = "Impala"
    MAHOUT = "Mahout"
    OOZIE = "Oozie"
    PHOENIX = "Phoenix"
    PRESTO = "Presto"
    S3 = "HDFS"
    SPARK = "Spark"
    SPARK_LIVY = "Livy"
    SQOOP = "Sqoop"
    SUPERSET = "Superset"
    TENSORFLOW = "TensorFlow"
    TEZ = "Tez"
    ZEPPELIN = "Zeppelin"
    ZOOKEEPER = "ZooKeeper"

    ALL = [AIRFLOW, AMBARI, HADOOP, GANGLIA, HBASE, HCATALOG, HIVE, HUE, IMPALA,
           MAHOUT, OOZIE, PHOENIX, PRESTO, S3, SPARK, SPARK_LIVY, SQOOP, SUPERSET,
           TENSORFLOW, TEZ, ZEPPELIN, ZOOKEEPER]
