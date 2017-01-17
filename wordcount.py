from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from ctapipe.image.cleaning import tailcuts_clean
from ctapipe.io import CameraGeometry
from ctapipe.image.hillas import hillas_parameters, HillasParameterizationError
from astropy import units as u

import msgpack
import msgpack_numpy as m
from ctapipe.reco.FitGammaHillas import FitGammaHillas
from ctapipe.io.hessio import hessio_event_source


source = hessio_event_source('gamma_test.simtel.gz', max_events=7)
instrument = next(source).inst
# Create a local StreamingContext with two working thread and batch interval of 1 second
sc = SparkContext('local[3]', 'test app')
broadcastInst = sc.broadcast(instrument)
ssc = StreamingContext(sc, 5)


def reco(single_telescope_data):
    fit = FitGammaHillas()
    inst = broadcastInst.value
    hillas_dict, tel_phi, tel_theta = single_telescope_data

    fit_result = fit.predict(hillas_dict, inst, tel_phi, tel_theta)
    return fit_result


def hillas(event):
    # print(event)
    hillas_dict = {}
    tel_phi = {}
    tel_theta = {}
    for tel in event:
        tel_id = tel['tel_id']
        tel_phi[tel_id] = 0.*u.deg
        tel_theta[tel_id] = 20.*u.deg

        pmt_signal = tel['adc_sums'][0]
        # print(pmt_signal)
        inst = broadcastInst.value
        pix_x = inst.pixel_pos[tel_id][0]
        pix_y = inst.pixel_pos[tel_id][1]
        foc = inst.optical_foclen[tel_id]
        cam_geom = CameraGeometry.guess(pix_x, pix_y, foc)
        mask = tailcuts_clean(cam_geom, pmt_signal, 1,
                              picture_thresh=10., boundary_thresh=5.)
        pmt_signal[mask == 0] = 0

        try:
            moments = hillas_parameters(cam_geom.pix_x,
                                        cam_geom.pix_y,
                                        pmt_signal)
            hillas_dict[tel['tel_id']] = moments
        except HillasParameterizationError as e:
            print(e)

    return (hillas_dict, tel_phi, tel_theta)


def decoder(d):
    d = msgpack.unpackb(d, encoding='utf8', object_hook=m.decode)
    return d


zkQuorum = 'localhost:2181'
dataStream = KafkaUtils.createStream(ssc=ssc,
                                     zkQuorum=zkQuorum,
                                     groupId='rta_group',
                                     topics={'data': 1},
                                     valueDecoder=decoder,
                                     kafkaParams={
                                      'metadata.broker.list': 'localhost:9092',
                                      'fetch.message.max.bytes': '104857600',
                                      })

# dataStream = ssc.

sums = dataStream.mapValues(hillas)\
                 .filter(lambda t: len(t[1][0]) > 2)\
                 .mapValues(reco)\
                 .count()
sums.pprint()

ssc.start()
ssc.awaitTerminationOrTimeout(timeout=600)

# ts = sc.parallelize(words, 2).map(lambda w: (w, 1))
# print(ts)
# counts = ts.reduceByKey(lambda b, c: b + c)
# sorted_counts = counts.sortBy(lambda k: k[1], ascending=False)
#
#
# print(sorted_counts.take(20))

#
# import sys
# from operator import add
#
# from pyspark.sql import SparkSession
#
#
# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: wordcount <file>", file=sys.stderr)
#         exit(-1)
#
#     spark = SparkSession\
#         .builder\
#         .appName("PythonWordCount")\
#         .getOrCreate()
#
#     lines = spark.read.text(sys.argv[1]).rdd.map(lambda r: r[0])
#     counts = lines.flatMap(lambda x: x.split(' ')) \
#                   .map(lambda x: (x, 1)) \
#                   .reduceByKey(add)
#     output = counts.collect()
#     for (word, count) in output:
#         print("%s: %i" % (word, count))
#
#     spark.stop()
