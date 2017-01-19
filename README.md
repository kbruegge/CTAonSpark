# CTAonSpark
This thing contains a kafka producer which produces CTA events to be pushed in
to a kafka stream.  
Testing to run CTA reconstruction on Apache Spark

#dockerized things

Start by building the spark image

```
docker build -t spark-standalone ./spark/
```
