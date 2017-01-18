# CTAonSpark
This thing contains a kafka producer which produces CTA events to be pushed in
to a kafka stream.  
Testing to run CTA reconstruction on Apache Spark

#Installation
Create a conda env with Python 3.5 and execute the following commands
```
conda install ctapipe -c cta-observatory
pip install py4j pykafka
wget http://d3kbcqa49mib13.cloudfront.net/spark-2.1.0-bin-hadoop2.7.tgz
mv spark-2.1.0-bin-hadoop2.7 spark
```

Then set two environment variables
```
SPARK_HOME=<path to spark>
PYTHONPATH=<path to spark>/python #I know this is ugly
```


Running this on a YARN cluster. On the cluster 10*8 cores right about now.
